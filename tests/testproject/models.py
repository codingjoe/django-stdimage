import os
from django.db import models
from stdimage import StdImageField


def upload_to(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return os.path.join('img', '%s.%s' % ('image', ext))


class SimpleModel(models.Model):
    """works as ImageField"""
    image = StdImageField(upload_to=upload_to)


class AdminDeleteModel(models.Model):
    """can be deleted through admin"""
    image = StdImageField(upload_to=upload_to, blank=True)


class ResizeModel(models.Model):
    """resizes image to maximum size to fit a 640x480 area"""
    image = StdImageField(upload_to=upload_to, variations={'medium': (600, 400), 'thumbnail': (100, 75)})


class ResizeCropModel(models.Model):
    """resizes image to 640x480 cropping if necessary"""
    image = StdImageField(upload_to=upload_to, variations={'medium': (600, 400, True)})


class ThumbnailModel(models.Model):
    """creates a thumbnail resized to maximum size to fit a 100x75 area"""
    image = StdImageField(upload_to=upload_to, blank=True, variations={'thumbnail': (100, 75)})


class ThumbnailCropModel(models.Model):
    """creates a thumbnail resized to 100x100 croping if necessary"""
    image = StdImageField(upload_to=upload_to, variations={'thumbnail': (100, 100, True)})


class MultipleFieldsModel(models.Model):
    """creates a thumbnail resized to 100x100 croping if necessary"""
    image1 = StdImageField(upload_to=upload_to, variations={'thumbnail': (100, 100, True)})
    image2 = StdImageField(upload_to=upload_to)
    image3 = StdImageField('Some label', upload_to=upload_to)
    text = models.CharField('Some label', max_length=10)


class MaxSizeModel(models.Model):
    image = StdImageField(upload_to=upload_to, max_size=(100, 100))

class AllModel(models.Model):
    """all previous features in one declaration"""
    image = StdImageField(upload_to=upload_to, blank=True,
                          variations={'large': (600, 400), 'thumbnail': (100, 100, True)})

class NewParamsModel(models.Model):
    """all previous features in one declaration"""
    image  = StdImageField(upload_to=upload_to, blank=True,
                           variations={'large': (600, 400), 'thumbnail': (100, 100, True), 'resized': (300, 200)})

    image1 = StdImageField(upload_to=upload_to, blank=True,
                           thumbnail_size=(100, 100, True),
                           variations={'large': {"width": 600, "height": 400}, 'resized': (300, 200)})

    image2 = StdImageField(upload_to=upload_to, blank=True,
                           thumbnail_size=(100, 100, True),
                           size=(300,200),
                           variations={'large': {"width": 600, "height": 400}})