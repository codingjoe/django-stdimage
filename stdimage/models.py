# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals)

from io import BytesIO
import logging
import os

from django.db.models import signals
from django.db.models.fields.files import ImageField, ImageFileDescriptor, \
    ImageFieldFile
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from .validators import MinSizeValidator


logger = logging.getLogger()


class StdImageFileDescriptor(ImageFileDescriptor):
    """
    The variation property of the field should be accessible in instance cases

    """

    def __set__(self, instance, value):
        super(StdImageFileDescriptor, self).__set__(instance, value)
        self.field.set_variations(instance)


class StdImageFieldFile(ImageFieldFile):
    """
    Like ImageFieldFile but handles variations.
    """

    def save(self, name, content, save=True):
        super(StdImageFieldFile, self).save(name, content, save)

        for key, variation in self.field.variations.items():
            self.render_and_save_variation(name, content, variation)

    @staticmethod
    def is_smaller(img, variation):
        return img.size[0] > variation['width'] \
            or img.size[1] > variation['height']

    def render_and_save_variation(self, name, content, variation,
                                  replace=False):
        """
        Renders the image variations and saves them to the storage
        """
        variation_name = self.get_variation_name(self.name, variation['name'])
        if self.storage.exists(variation_name):
            if replace:
                self.storage.delete(variation_name)
                logger.info('File "{}" already exists and has been replaced.')
            else:
                logger.info('File "{}" already exists.')
                return variation_name

        content.seek(0)

        resample = variation['resample']

        with Image.open(content) as img:
            file_format = img.format

            if self.is_smaller(img, variation):
                factor = 1
                while (img.size[0] / factor
                        > 2 * variation['width']
                       and img.size[1] * 2 / factor
                        > 2 * variation['height']):
                    factor *= 2
                if factor > 1:
                    img.thumbnail(
                        (int(img.size[0] / factor),
                         int(img.size[1] / factor)),
                        resample=resample
                    )

                if variation['crop']:
                    img = ImageOps.fit(
                        img,
                        (variation['width'], variation['height']),
                        method=resample
                    )
                else:
                    img.thumbnail(
                        (variation['width'], variation['height']),
                        resample=resample
                    )

            with BytesIO() as file_buffer:
                img.save(file_buffer, file_format, quality=variation['quality'])
                f = ContentFile(file_buffer.getvalue())
                self.storage.save(variation_name, f)
        return variation_name

    @classmethod
    def get_variation_name(cls, file_name, variation_name):
        """
        Returns the variation file name based on the model
        it's field and it's variation.
        """
        ext = cls.get_file_extension(file_name)
        path = file_name.rsplit('/', 1)[0]
        file_name = file_name.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        file_name = '{file_name}.{variation_name}{extension}'.format(**{
            'file_name': file_name,
            'variation_name': variation_name,
            'extension': ext,
        })
        return os.path.join(path, file_name)

    @staticmethod
    def get_file_extension(filename):
        """
        Returns the file extension.
        """
        return os.path.splitext(filename)[1].lower()

    def delete(self, save=True):
        self.delete_variations()
        super(StdImageFieldFile, self).delete(save)

    def delete_variations(self):
        for variation in self.field.variations:
            variation_name = self.get_variation_name(self.name, variation)
            self.storage.delete(variation_name)


class StdImageField(ImageField):
    """
    Django field that behaves as ImageField, with some extra features like:
        - Auto resizing
        - Allow image deletion

    :param variations: size variations of the image
    """
    descriptor_class = StdImageFileDescriptor
    attr_class = StdImageFieldFile
    def_variation = {
        'width': float('inf'),
        'height': float('inf'),
        'crop': False,
        'resample': Image.ANTIALIAS,
        'quality': 75,
    }

    def __init__(self, verbose_name=None, name=None, variations=None,
                 force_min_size=False, *args, **kwargs):
        """
        Standardized ImageField for Django
        Usage: StdImageField(upload_to='PATH',
         variations={'thumbnail': {"width", "height", "crop", "resample"}})
        :param variations: size variations of the image
        :rtype variations: StdImageField
        """
        if not variations:
            variations = {}
        if not isinstance(variations, dict):
            raise TypeError('"variations" must be of type dict.')
        self._variations = variations
        self.force_min_size = force_min_size
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

        super(StdImageField, self).__init__(verbose_name, name,
                                            *args, **kwargs)

    def add_variation(self, name, params):
        variation = self.def_variation.copy()
        if isinstance(params, (list, tuple)):
            variation.update(dict(zip(("width", "height", "crop", "quality"), params)))
        else:
            variation.update(params)
        variation["name"] = name
        self.variations[name] = variation

    def set_variations(self, instance=None, **kwargs):
        """
        Creates a "variation" object as attribute of the ImageField instance.
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
        """Call methods for generating all operations on specified signals"""
        super(StdImageField, self).contribute_to_class(cls, name)
        signals.post_init.connect(self.set_variations, sender=cls)

    def validate(self, value, model_instance):
        super(StdImageField, self).validate(value, model_instance)
        if self.force_min_size:
            MinSizeValidator(self.min_size[0], self.min_size[1])(value)


try:
    from south.modelsinspector import add_introspection_rules

    add_introspection_rules([], ["^stdimage\.models\.StdImageField"])
except ImportError:
    pass
