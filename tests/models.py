from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.signals import post_delete, pre_save
from PIL import Image

from stdimage import StdImageField
from stdimage.models import StdImageFieldFile
from stdimage.utils import (
    UploadTo, UploadToAutoSlugClassNameDir, UploadToUUID,
    pre_delete_delete_callback, pre_save_delete_callback, render_variations
)
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


class MyStorageModel(CustomManagerModel):
    """delays creation of 150x150 thumbnails until it is called manually"""
    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        variations={'thumbnail': (150, 150, True)},
        storage=FileSystemStorage(),
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


def custom_render_variations(file_name, variations, storage, replace=False):
    """Resize image to 100x100."""
    for _, variation in variations.items():
        variation_name = StdImageFieldFile.get_variation_name(
            file_name,
            variation['name']
        )
        if storage.exists(variation_name):
            storage.delete(variation_name)

        with storage.open(file_name) as f:
            with Image.open(f) as img:
                size = 100, 100
                img = img.resize(size)

                with BytesIO() as file_buffer:
                    img.save(file_buffer, 'JPEG')
                    f = ContentFile(file_buffer.getvalue())
                    storage.save(variation_name, f)

    return False


class CustomRenderVariationsModel(models.Model):
    """Use custom render_variations."""

    image = StdImageField(
        upload_to=UploadTo(name='image', path='img'),
        variations={'thumbnail': (150, 150)},
        render_variations=custom_render_variations,
    )


post_delete.connect(pre_delete_delete_callback, sender=SimpleModel)
pre_save.connect(pre_save_delete_callback, sender=AdminDeleteModel)
