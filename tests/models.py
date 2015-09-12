from django.db import models
from django.db.models.signals import post_delete, pre_save

from stdimage import StdImageField
from stdimage.utils import (UploadTo, UploadToAutoSlugClassNameDir,
                            UploadToUUID, pre_delete_delete_callback,
                            pre_save_delete_callback, render_variations)
from stdimage.validators import MaxSizeValidator, MinSizeValidator


class SimpleModel(models.Model):
    """works as ImageField"""
    image = StdImageField(upload_to='img/')


class AdminDeleteModel(models.Model):
    """can be deleted through admin"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        blank=True
    )


class ResizeModel(models.Model):
    """resizes image to maximum size to fit a 640x480 area"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        variations={
            'medium': {'width': 400, 'height': 400},
            'thumbnail': (100, 75),
        }
    )


class ResizeCropModel(models.Model):
    """resizes image to 640x480 cropping if necessary"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        variations={'thumbnail': (150, 150, True)}
    )


class ThumbnailModel(models.Model):
    """creates a thumbnail resized to maximum size to fit a 100x75 area"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        blank=True,
        variations={'thumbnail': (100, 75)}
    )


class MaxSizeModel(models.Model):
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        validators=[MaxSizeValidator(16, 16)]
    )


class MinSizeModel(models.Model):
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        validators=[MinSizeValidator(200, 200)]
    )


class ForceMinSizeModel(models.Model):
    """creates a thumbnail resized to maximum size to fit a 100x75 area"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        force_min_size=True,
        variations={'thumbnail': (600, 600)}
    )


class AutoSlugClassNameDirModel(models.Model):
    name = models.CharField(max_length=50)
    image = StdImageField(
        upload_to=UploadToAutoSlugClassNameDir(populate_from='name')
    )


class UUIDModel(models.Model):
    image = StdImageField(upload_to=UploadToUUID(path='img'))


class CustomManager(models.Manager):
    """Just like Django's default, but a different class."""
    pass


class CustomManagerModel(models.Model):
    customer_manager = CustomManager()

    class Meta:
        abstract = True


class ManualVariationsModel(CustomManagerModel):
    """delays creation of 150x150 thumbnails until it is called manually"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        variations={'thumbnail': (150, 150, True)},
        render_variations=False
    )


def render_job(**kwargs):
    render_variations(**kwargs)
    return False


class UtilVariationsModel(models.Model):
    """delays creation of 150x150 thumbnails until it is called manually"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        variations={'thumbnail': (150, 150, True)},
        render_variations=render_job
    )


class ThumbnailWithoutDirectoryModel(models.Model):
    """Save into a generated filename that does not contain any '/' char"""
    image = StdImageField(
        upload_to=lambda instance, filename: 'custom.gif',
        variations={'thumbnail': {'width': 150, 'height': 150}},
    )

post_delete.connect(pre_delete_delete_callback, sender=SimpleModel)
pre_save.connect(pre_save_delete_callback, sender=AdminDeleteModel)
