# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals)

import uuid
from django.utils.text import slugify
from django.utils.deconstruct import deconstructible

import os
from .models import StdImageField


@deconstructible
class UploadTo(object):
    file_pattern = "%(name)s.%(ext)s"
    path_pattern = "%(path)s"

    def __call__(self, instance, filename):
        defaults = {
            'ext': filename.rsplit('.', 1)[1],
            'name': filename.rsplit('.', 1)[0],
            'path': filename.rsplit('/', 1)[0],
            'class_name': instance.__class__.__name__,
        }
        defaults.update(self.kwargs)
        return os.path.join(self.path_pattern % defaults,
                            self.file_pattern % defaults).lower()

    def __init__(self, **kwargs):
        self.kwargs = kwargs


@deconstructible
class UploadToUUID(UploadTo):

    def __call__(self, instance, filename):
        self.kwargs.update({
            'name': uuid.uuid4().hex,
        })
        return super(UploadToUUID, self).__call__(instance, filename)


@deconstructible
class UploadToClassNameDir(UploadTo):
    path_pattern = '%(class_name)s'


@deconstructible
class UploadToClassNameDirUUID(UploadToClassNameDir, UploadToUUID):
    pass


@deconstructible
class UploadToAutoSlug(UploadTo):

    def __init__(self, populate_from, **kwargs):
        self.populate_from = populate_from
        super(UploadToAutoSlug, self).__init__(**kwargs)

    def __call__(self, instance, filename):
        field_value = getattr(instance, self.populate_from)
        self.kwargs.update({
            'name': slugify(field_value),
        })
        return super(UploadToAutoSlug, self).__call__(instance, filename)


@deconstructible
class UploadToAutoSlugClassNameDir(UploadToClassNameDir, UploadToAutoSlug):
    pass


def pre_delete_delete_callback(sender, instance, **kwargs):
    for field in instance._meta.fields:
        if isinstance(field, StdImageField):
            getattr(instance, field.name).delete()


def pre_save_delete_callback(sender, instance, **kwargs):
    if instance.pk:
        obj = sender.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            if isinstance(field, StdImageField):
                obj_field = getattr(obj, field.name)
                instance_field = getattr(instance, field.name)
                if obj_field and not instance_field:
                    obj_field.delete(False)
