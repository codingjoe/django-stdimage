# -*- coding: utf-8 -*-
import os
from io import BytesIO
from django.db.models import signals
from django.db.models.fields.files import ImageField, ImageFileDescriptor, ImageFieldFile
from django.core.files.base import ContentFile
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings

try:
    import Image, ImageOps
except ImportError:
    from PIL import Image, ImageOps

from .forms import StdImageFormField
from .widgets import DelAdminFileWidget
from .utils import upload_to_class_name_dir, upload_to_class_name_dir_uuid, upload_to_uuid

UPLOAD_TO_CLASS_NAME = upload_to_class_name_dir
UPLOAD_TO_CLASS_NAME_UUID = upload_to_class_name_dir_uuid
UPLOAD_TO_UUID = upload_to_uuid


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

        for variation in self.field.variations:
            self.render_and_save_variation(name, content, variation)

    @staticmethod
    def is_smaller(img, variation):
        return img.size[0] > variation['width'] or img.size[1] > variation['height']

    def render_and_save_variation(self, name, content, variation):
        """
        Renders the image variations and saves them to the storage
        """
        resample = variation['resample'] or Image.ANTIALIAS

        content.seek(0)

        img = Image.open(content)

        if self.is_smaller(img, variation):
            factor = 1
            while (img.size[0] / factor > 2 * variation['width'] and
                                   img.size[1] * 2 / factor > 2 * variation['height']):
                factor *= 2
            if factor > 1:
                img.thumbnail((int(img.size[0] / factor),
                               int(img.size[1] / factor)), resample=resample)

            if variation['crop']:
                img = ImageOps.fit(img, (variation['width'], variation['height']), method=resample)
            else:
                img.thumbnail((variation['width'], variation['height']), resample=resample)
        variation_name = self.get_variation_name(self.instance, self.field, variation)
        file_buffer = StringIO()
        format = self.get_file_extension(name).lower().replace('jpg', 'jpeg')
        img.save(file_buffer, format)
        self.storage.save(variation_name, ContentFile(file_buffer.getvalue()))
        file_buffer.close()

    @classmethod
    def get_variation_name(cls, instance, field, variation):
        """
        Returns the variation file name based on the model it's field and it's variation
        """
        field = getattr(instance, field.name)
        name = field.name
        ext = cls.get_file_extension(name)
        file_name = name.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        path = name.rsplit('/', 1)[0]

        return os.path.join(path, '%s.%s.%s' % (file_name, variation['name'], ext))

    @staticmethod
    def get_file_extension(name):
        """
        Returns the file extension.
        """
        filename_split = name.rsplit('.', 1)
        return filename_split[-1]

    def delete(self, save=True):
        for variation in self.field.variations:
            variation_name = self.get_variation_name(self.name, variation)
            self.storage.delete(variation_name)

        super(StdImageFieldFile, self).delete(save)


class StdImageField(ImageField):
    """
    Django field that behaves as ImageField, with some extra features like:
        - Auto resizing
        - Allow image deletion

    :param variations: size variations of the image
    """
    descriptor_class = StdImageFileDescriptor

    attr_class = StdImageFieldFile

    def __init__(self, verbose_name=None, name=None, variations={}, min_size=None, max_size=None, *args, **kwargs):
        """
        Standardized ImageField for Django
        Usage: StdImageField(upload_to='PATH', variations={'thumbnail': (width, height, boolean, algorithm)})
        :param variations: size variations of the image
        :rtype variations: StdImageField
        """

        param_size = ('width', 'height', 'crop', 'resample')
        self.variations = []
        self.min_size = {'width': 0, 'height': 0}
        self.max_size = {'width': float('inf'), 'height': float('inf')}

        for key, attr in variations.iteritems():
            if attr and isinstance(attr, (tuple, list)):
                variation = dict(zip(param_size, attr))
                variation['name'] = key
                setattr(self, key, variation)
                self.variations.append(variation)
            else:
                setattr(self, key, None)

        if 'django.contrib.admin' in settings.INSTALLED_APPS and not hasattr(self.variations, 'admin'):
            self.variations.append({'name': 'admin',
                                    'width': 100,
                                    'height': 100,
                                    'crop': False,
                                    'resample': Image.NEAREST})

        if not min_size:  # min_size gets set to biggest variation
            for variation in self.variations:
                if variation['width'] > self.min_size['width']:
                    self.min_size['width'] = variation['width']
                if variation['height'] > self.min_size['height']:
                    self.min_size['height'] = variation['height']
        else:
            self.min_size['width'] = min_size[0]
            self.min_size['height'] = min_size[1]

        if max_size:
            self.max_size['width'] = max_size[0]
            self.max_size['height'] = max_size[1]

        super(StdImageField, self).__init__(verbose_name, name, *args, **kwargs)

    def set_variations(self, instance=None, **kwargs):
        """
        Creates a "variation" object as attribute of the ImageField instance.
        Variation attribute will be of the same class as the original image, so
        "path", "url"... properties can be used

        :param instance: FileField
        """
        if getattr(instance, self.name):
            field = getattr(instance, self.name)
            for variation in self.variations:
                variation_name = self.attr_class.get_variation_name(instance, self, variation)
                variation_field = ImageFieldFile(instance, self, variation_name)
                setattr(field, variation['name'], variation_field)

    def save_form_data(self, instance, data):
        """
        Overwrite save_form_data to delete images if "delete" checkbox is selected

        :param instance: Form
        """
        if data == '__deleted__':
            name = getattr(instance, self.name).name
            self.storage.delete(name)
            for variation in self.variations:
                variation_name = self.attr_class.get_variation_name(instance, self, variation)
                self.storage.delete(variation_name)
        else:
            super(StdImageField, self).save_form_data(instance, data)

    def formfield(self, **kwargs):
        """Specify form field and widget to be used on the forms"""
        kwargs['widget'] = DelAdminFileWidget
        kwargs['form_class'] = StdImageFormField
        return super(StdImageField, self).formfield(**kwargs)

    def get_db_prep_save(self, value, connection=None):
        """Overwrite get_db_prep_save to allow saving nothing to the database if image has been deleted"""
        if value:
            return super(StdImageField, self).get_db_prep_save(value, connection=connection)
        else:
            return u''

    def contribute_to_class(self, cls, name):
        """Call methods for generating all operations on specified signals"""

        super(StdImageField, self).contribute_to_class(cls, name)
        signals.post_init.connect(self.set_variations, sender=cls)

    def validate(self, value, model_instance):
        super(StdImageField, self).validate(value, model_instance)
        if hasattr(value, 'file'):  # fails if file has been deleted.
            value.seek(0)
            stream = StringIO(value.read())
            img = Image.open(stream)
            if img.size[0] < self.min_size['width'] or img.size[1] < self.min_size['height']:
                raise ValidationError(
                    _('The image you uploaded is too small. The required minimal resolution is: %sx%s px.') %
                    (self.min_size['width'], self.min_size['height']))
            elif img.size[0] > self.max_size['width'] or img.size[1] > self.max_size['height']:
                raise ValidationError(
                    _('The image you uploaded is too large. The required maximal resolution is: %sx%s px.') %
                    (self.max_size['width'], self.max_size['height']))
