import logging
import os
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import signals
from django.db.models.fields.files import (
    ImageField, ImageFieldFile, ImageFileDescriptor
)
from PIL import Image, ImageOps

from .validators import MinSizeValidator

logger = logging.getLogger()


class StdImageFileDescriptor(ImageFileDescriptor):
    """The variation property of the field is accessible in instance cases."""

    def __set__(self, instance, value):
        super(StdImageFileDescriptor, self).__set__(instance, value)
        self.field.set_variations(instance)


class StdImageFieldFile(ImageFieldFile):
    """Like ImageFieldFile but handles variations."""

    def save(self, name, content, save=True):
        super().save(name, content, save)
        render_variations = self.field.render_variations
        if callable(render_variations):
            render_variations = render_variations(
                file_name=self.name,
                variations=self.field.variations,
                storage=self.storage,
            )
        if not isinstance(render_variations, bool):
            msg = (
                '"render_variations" callable expects a boolean return value,'
                ' but got %s'
                ) % type(render_variations)
            raise TypeError(msg)
        if render_variations:
            self.render_variations()

    @staticmethod
    def is_smaller(img, variation):
        return img.size[0] > variation['width'] \
            or img.size[1] > variation['height']

    def render_variations(self, replace=False):
        """Render all image variations and saves them to the storage."""
        for _, variation in self.field.variations.items():
            self.render_variation(self.name, variation, replace, self.storage)

    @classmethod
    def render_variation(cls, file_name, variation, replace=False,
                         storage=default_storage):
        """Render an image variation and saves it to the storage."""
        variation_name = cls.get_variation_name(file_name, variation['name'])
        if storage.exists(variation_name):
            if replace:
                storage.delete(variation_name)
                logger.info('File "{}" already exists and has been replaced.')
            else:
                logger.info('File "{}" already exists.')
                return variation_name

        resample = variation['resample']

        with storage.open(file_name) as f:
            with Image.open(f) as img:
                save_kargs = {}
                file_format = img.format

                if cls.is_smaller(img, variation):
                    factor = 1
                    while img.size[0] / factor \
                            > 2 * variation['width'] \
                            and img.size[1] * 2 / factor \
                            > 2 * variation['height']:
                        factor *= 2
                    if factor > 1:
                        img.thumbnail(
                            (int(img.size[0] / factor),
                             int(img.size[1] / factor)),
                            resample=resample
                        )

                    size = variation['width'], variation['height']
                    size = tuple(int(i) if i != float('inf') else i
                                 for i in size)

                    if file_format == 'JPEG':
                        # http://stackoverflow.com/a/21669827
                        img = img.convert('RGB')
                        save_kargs['optimize'] = True
                        save_kargs['quality'] = 'web_high'
                        if size[0] * size[1] > 10000:  # roughly <10kb
                            save_kargs['progressive'] = True

                    if variation['crop']:
                        img = ImageOps.fit(
                            img,
                            size,
                            method=resample
                        )
                    else:
                        img.thumbnail(
                            size,
                            resample=resample
                        )

                with BytesIO() as file_buffer:
                    img.save(file_buffer, file_format, **save_kargs)
                    f = ContentFile(file_buffer.getvalue())
                    storage.save(variation_name, f)
        return variation_name

    @classmethod
    def get_variation_name(cls, file_name, variation_name):
        """Return the variation file name based on the variation."""
        path, ext = os.path.splitext(file_name)
        path, file_name = os.path.split(path)
        file_name = '{file_name}.{variation_name}{extension}'.format(**{
            'file_name': file_name,
            'variation_name': variation_name,
            'extension': ext,
        })
        return os.path.join(path, file_name)

    def delete(self, save=True):
        self.delete_variations()
        super().delete(save)

    def delete_variations(self):
        for variation in self.field.variations:
            variation_name = self.get_variation_name(self.name, variation)
            self.storage.delete(variation_name)


class StdImageField(ImageField):
    """
    Django ImageField that is able to create different size variations.

    Extra features are:
        - Django-Storages compatible (S3)
        - Python 2, 3 and PyPy support
        - Django 1.5 and later support
        - Resize images to different sizes
        - Access thumbnails on model level, no template tags required
        - Preserves original image
        - Asynchronous rendering (Celery & Co)
        - Multi threading and processing for optimum performance
        - Restrict accepted image dimensions
        - Rename files to a standardized name (using a callable upload_to)

    :param variations: size variations of the image
    """

    descriptor_class = StdImageFileDescriptor
    attr_class = StdImageFieldFile
    def_variation = {
        'width': float('inf'),
        'height': float('inf'),
        'crop': False,
        'resample': Image.ANTIALIAS
    }

    def __init__(self, verbose_name=None, name=None, variations=None,
                 render_variations=True, force_min_size=False,
                 *args, **kwargs):
        """
        Standardized ImageField for Django.

        Usage: StdImageField(upload_to='PATH',
         variations={'thumbnail': {"width", "height", "crop", "resample"}})
        :param variations: size variations of the image
        :rtype variations: StdImageField
        :param render_variations: boolean or callable that returns a boolean.
         The callable gets passed the app_name, model, field_name and pk.
         Default: True
        :rtype render_variations: bool, callable
        """
        if not variations:
            variations = {}
        if not isinstance(variations, dict):
            msg = ('"variations" expects a dict,'
                   ' but got %s') % type(variations)
            raise TypeError(msg)
        if not (isinstance(render_variations, bool) or
                callable(render_variations)):
            msg = ('"render_variations" excepts a boolean or callable,'
                   ' but got %s') % type(render_variations)
            raise TypeError(msg)

        self._variations = variations
        self.force_min_size = force_min_size
        self.render_variations = render_variations
        self.variations = {}

        for nm, prm in list(variations.items()):
            self.add_variation(nm, prm)

        if self.variations and self.force_min_size:
            self.min_size = (
                max(self.variations.values(),
                    key=lambda x: x["width"])["width"],
                max(self.variations.values(),
                    key=lambda x: x["height"])["height"]
            )

        super().__init__(verbose_name, name, *args, **kwargs)

    def add_variation(self, name, params):
        variation = self.def_variation.copy()
        if isinstance(params, (list, tuple)):
            variation.update(dict(zip(("width", "height", "crop"), params)))
        else:
            variation.update(params)
        variation["name"] = name
        self.variations[name] = variation

    def set_variations(self, instance=None, **kwargs):
        """
        Create a "variation" object as attribute of the ImageField instance.

        Variation attribute will be of the same class as the original image, so
        "path", "url"... properties can be used

        :param instance: FileField
        """
        if getattr(instance, self.name):
            field = getattr(instance, self.name)
            if field._committed:
                for name, variation in list(self.variations.items()):
                    variation_name = self.attr_class.get_variation_name(
                        field.name,
                        variation['name']
                    )
                    variation_field = ImageFieldFile(instance,
                                                     self,
                                                     variation_name)
                    setattr(field, name, variation_field)

    def contribute_to_class(self, cls, name):
        """Generate all operations on specified signals."""
        super().contribute_to_class(cls, name)
        signals.post_init.connect(self.set_variations, sender=cls)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if self.force_min_size:
            MinSizeValidator(self.min_size[0], self.min_size[1])(value)
