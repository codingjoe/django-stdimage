[![Django-CC](https://img.shields.io/badge/Django-CC-ee66dd.svg)](https://github.com/codingjoe/django-cc)
[![version](https://img.shields.io/pypi/v/django-stdimage.svg)](https://pypi.python.org/pypi/django-stdimage/)
[![ci](https://api.travis-ci.org/codingjoe/django-stdimage.svg?branch=master)](https://travis-ci.org/codingjoe/django-stdimage)
[![codecov](https://codecov.io/gh/codingjoe/django-stdimage/branch/master/graph/badge.svg)](https://codecov.io/gh/codingjoe/django-stdimage)
[![code-health](https://landscape.io/github/codingjoe/django-stdimage/master/landscape.svg?style=flat)](https://landscape.io/github/codingjoe/django-stdimage/master)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

# Django Standardized Image Field

Django Field that implement the following features:

* Django-Storages compatible (S3)
* Resize images to different sizes
* Access thumbnails on model level, no template tags required
* Preserves original image
* Asynchronous rendering (Celery & Co)
* Multi threading and processing for optimum performance
* Restrict accepted image dimensions
* Rename files to a standardized name (using a callable upload_to)

## Installation

Simply install the latest stable package using the command

`pip install django-stdimage`

and add `'stdimage'` to `INSTALLED_APP`s in your settings.py, that's it!

## Usage


``StdImageField`` works just like Django's own
[ImageField](https://docs.djangoproject.com/en/dev/ref/models/fields/#imagefield)
except that you can specify different sized variations.

### Variations
Variations are specified withing a dictionary. The key will will be the attribute referencing the resized image.
A variation can be defined both as a tuple or a dictionary.

Example:
```python
from stdimage.models import StdImageField


class MyModel(models.Model):
    # works just like django's ImageField
    image = StdImageField(upload_to='path/to/img')

    # creates a thumbnail resized to maximum size to fit a 100x75 area
    image = StdImageField(upload_to='path/to/img',
                          variations={'thumbnail': {'width': 100, 'height': 75}})

    # is the same as dictionary-style call
    image = StdImageField(upload_to='path/to/img', variations={'thumbnail': (100, 75)})

    # creates a thumbnail resized to 100x100 croping if necessary
    image = StdImageField(upload_to='path/to/img', variations={
        'thumbnail': {"width": 100, "height": 100, "crop": True}
    })

    ## Full ammo here. Please note all the definitions below are equal
    image = StdImageField(upload_to=upload_to, blank=True, variations={
        'large': (600, 400),
        'thumbnail': (100, 100, True),
        'medium': (300, 200),
    })
```

 For using generated variations in templates use `myimagefield.variation_name`.

Example:
```html
<a href="{{ object.myimage.url }}"><img alt="" src="{{ object.myimage.thumbnail.url }}"/></a>
```

### Utils
By default StdImageField stores images without modifying the file name.
If you want to use more consistent file names you can use the build in upload callables.

Example:
```python
from stdimage.utils import UploadToUUID, UploadToClassNameDir, UploadToAutoSlug, \
    UploadToAutoSlugClassNameDir


class MyClass(models.Model):
    title = models.CharField(max_length=50)

    # Gets saved to MEDIA_ROOT/myclass/#FILENAME#.#EXT#
    image1 = StdImageField(upload_to=UploadToClassNameDir())

    # Gets saved to MEDIA_ROOT/myclass/pic.#EXT#
    image2 = StdImageField(upload_to=UploadToClassNameDir(name='pic'))

    # Gets saved to MEDIA_ROOT/images/#UUID#.#EXT#
    image3 = StdImageField(upload_to=UploadToUUID(path='images'))

    # Gets saved to MEDIA_ROOT/myclass/#UUID#.#EXT#
    image4 = StdImageField(upload_to=UploadToClassNameDirUUID())

    # Gets save to MEDIA_ROOT/images/#SLUG#.#EXT#
    image5 = StdImageField(upload_to=UploadToAutoSlug(populate_from='title'))

    # Gets save to MEDIA_ROOT/myclass/#SLUG#.#EXT#
    image6 = StdImageField(upload_to=UploadToAutoSlugClassNameDir(populate_from='title'))
```

### Validators
The `StdImageField` doesn't implement any size validation. Validation can be specified using the validator attribute
and using a set of validators shipped with this package.
Validators can be used for both Forms and Models.

 Example
```python
from stdimage.validators import MinSizeValidator, MaxSizeValidator


class MyClass(models.Model)
    image1 = StdImageField(validators=[MinSizeValidator(800, 600)])
    image2 = StdImageField(validators=[MaxSizeValidator(1028, 768)])
```

**CAUTION:** The MaxSizeValidator should be used with caution.
As storage isn't expensive, you shouldn't restrict upload dimensions.
If you seek prevent users form overflowing your memory you should restrict the HTTP upload body size.

### Deleting images
Django [dropped support](https://docs.djangoproject.com/en/dev/releases/1.3/#deleting-a-model-doesn-t-delete-associated-files)
for automated deletions in version 1.3.
Implementing file deletion [should be done](http://stackoverflow.com/questions/5372934/how-do-i-get-django-admin-to-delete-files-when-i-remove-an-object-from-the-data)
inside your own applications using the `post_delete` or `pre_delete` signal.
Clearing the field if blank is true, does not delete the file. This can also be achieved using `pre_save` and `post_save` signals.
This packages contains two signal callback methods that handle file deletion for all SdtImageFields of a model.

```python
from stdimage.utils import pre_delete_delete_callback, pre_save_delete_callback


post_delete.connect(pre_delete_delete_callback, sender=MyModel)
pre_save.connect(pre_save_delete_callback, sender=MyModel)
```

**Warning:** You should not use the signal callbacks in production. They may result in data loss.


### Async image processing
Tools like celery allow to execute time-consuming tasks outside of the request. If you don't want
to wait for your variations to be rendered in request, StdImage provides your the option to pass a
async keyword and a util.
Note that the callback is not transaction save, but the file will be there.
This example is based on celery.

`tasks.py`:
```python
try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    from django.db.models.loading import get_model

from celery import shared_task

from stdimage.utils import render_variations


@shared_task
def process_photo_image(file_name, variations, storage):
    render_variations(file_name, variations, replace=True, storage=storage)
    obj = get_model('myapp', 'Photo').objects.get(image=file_name)
    obj.processed = True
    obj.save()
```

`models.py`:
```python
from django.db import models
from stdimage.models import StdImageField
from stdimage.utils import UploadToClassNameDir

from tasks import process_photo_image

def image_processor(file_name, variations, storage):
    process_photo_image.delay(file_name, variations, storage)
    return False  # prevent default rendering

class AsyncImageModel(models.Model)
    image = StdImageField(
        # above task definition can only handle one model object per image filename
        upload_to=UploadToClassNameDir(),
        render_variations=image_processor  # pass boolean or callable
    )
    processed = models.BooleanField(default=False)  # flag that could be used for view querysets
```

### Re-rendering variations
You might want to add new variations to a field. That means you need to render new variations for missing fields.
This can be accomplished using a management command.
```bash
python manage.py rendervariations 'app_name.model_name.field_name' [--replace]
```
The `replace` option will replace all existing files.

### Multi processing
Since version 2 stdImage supports multiprocessing.
Every image is rendered in separate process.
It not only increased performance but the garbage collection
and therefore the huge memory footprint from previous versions.

**Note:** PyPy seems to have some problems regarding multiprocessing,
for that matter all multiprocessing is disabled in PyPy.

## [Contributing](CONTRIBUTING.md)

## [License](LICENSE)
