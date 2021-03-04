[![version](https://img.shields.io/pypi/v/django-stdimage.svg)](https://pypi.python.org/pypi/django-stdimage/)
[![ci](https://api.travis-ci.org/codingjoe/django-stdimage.svg?branch=master)](https://travis-ci.org/codingjoe/django-stdimage)
[![codecov](https://codecov.io/gh/codingjoe/django-stdimage/branch/master/graph/badge.svg)](https://codecov.io/gh/codingjoe/django-stdimage)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

# Django Standardized Image Field

Django Field that implement the following features:

* Django-Storages compatible (S3)
* Resize images to different sizes
* Access thumbnails on model level, no template tags required
* Preserves original image
* Asynchronous rendering (Celery & Co)
* Restrict accepted image dimensions
* Rename files to a standardized name (using a callable upload_to)

## Installation

Simply install the latest stable package using the command

```bash
pip install django-stdimage
# or
pipenv install django-stdimage
```

and add `'stdimage'` to `INSTALLED_APP`s in your settings.py, that's it!

## Usage

`StdImageField` works just like Django's own
[ImageField](https://docs.djangoproject.com/en/dev/ref/models/fields/#imagefield)
except that you can specify different sized variations.

The `JPEGField` works similar to the `StdImageField` but all size variations are
converted to JPEGs, no matter what type the original file is.

### Variations

Variations are specified within a dictionary. The key will be the attribute referencing the resized image.
A variation can be defined both as a tuple or a dictionary.

Example:

```python
from django.db import models
from stdimage import StdImageField, JPEGField


class MyModel(models.Model):
    # works just like django's ImageField
    image = StdImageField(upload_to='path/to/img')

    # creates a thumbnail resized to maximum size to fit a 100x75 area
    image = StdImageField(upload_to='path/to/img',
                          variations={'thumbnail': {'width': 100, 'height': 75}})

    # is the same as dictionary-style call
    image = StdImageField(upload_to='path/to/img', variations={'thumbnail': (100, 75)})

    # variations are converted to JPEGs
    jpeg = JPEGField(
        upload_to='path/to/img',
        variations={'full': (None, None), 'thumbnail': (100, 75)},
    )

    # creates a thumbnail resized to 100x100 croping if necessary
    image = StdImageField(upload_to='path/to/img', variations={
        'thumbnail': {"width": 100, "height": 100, "crop": True}
    })

    ## Full ammo here. Please note all the definitions below are equal
    image = StdImageField(upload_to='path/to/img', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (100, 100, True),
        'medium': (300, 200),
    }, delete_orphans=True)
```

For using generated variations in templates use `myimagefield.variation_name`.

Example:

```html
<a href="{{ object.myimage.url }}"><img alt="" src="{{ object.myimage.thumbnail.url }}"/></a>
```

### Utils

Since version 4 the custom `upload_to` utils have been dropped in favor of
[Django Dynamic Filenames][dynamic_filenames].

[dynamic_filenames]: https://github.com/codingjoe/django-dynamic-filenames

### Validators
The `StdImageField` doesn't implement any size validation. Validation can be specified using the validator attribute
and using a set of validators shipped with this package.
Validators can be used for both Forms and Models.

Example

```python
from django.db import models
from stdimage.validators import MinSizeValidator, MaxSizeValidator
from stdimage.models import StdImageField


class MyClass(models.Model):
    image1 = StdImageField(validators=[MinSizeValidator(800, 600)])
    image2 = StdImageField(validators=[MaxSizeValidator(1028, 768)])
```

**CAUTION:** The MaxSizeValidator should be used with caution.
As storage isn't expensive, you shouldn't restrict upload dimensions.
If you seek prevent users form overflowing your memory you should restrict the HTTP upload body size.

### Deleting images

Django [dropped support](https://docs.djangoproject.com/en/dev/releases/1.3/#deleting-a-model-doesn-t-delete-associated-files)
for automated deletions in version 1.3.

Since version 5, this package supports a `delete_orphans` argument. It will delete
orphaned files, should a file be delete or replaced via Django form or and object with
a `StdImageField` be deleted. It will not be deleted if the field value is changed or
reassigned programatically. In those rare cases, you will need to handle proper deletion
yourself.

```python
from django.db import models
from stdimage.models import StdImageField


class MyModel(models.Model):
    image = StdImageField(
        upload_to='path/to/files',
        variations={'thumbnail': (100, 75)},
        delete_orphans=True,
        blank=True,
    )
```

### Async image processing
Tools like celery allow to execute time-consuming tasks outside of the request. If you don't want
to wait for your variations to be rendered in request, StdImage provides your the option to pass a
async keyword and a util.
Note that the callback is not transaction save, but the file will be there.
This example is based on celery.

`tasks.py`:
```python
from django.apps import apps

from celery import shared_task

from stdimage.utils import render_variations


@shared_task
def process_photo_image(file_name, variations, storage):
    render_variations(file_name, variations, replace=True, storage=storage)
    obj = apps.get_model('myapp', 'Photo').objects.get(image=file_name)
    obj.processed = True
    obj.save()
```

`models.py`:
```python
from django.db import models
from stdimage.models import StdImageField

from .tasks import process_photo_image

def image_processor(file_name, variations, storage):
    process_photo_image.delay(file_name, variations, storage)
    return False  # prevent default rendering

class AsyncImageModel(models.Model):
    image = StdImageField(
        # above task definition can only handle one model object per image filename
        upload_to='path/to/file/',
        render_variations=image_processor  # pass boolean or callable
    )
    processed = models.BooleanField(default=False)  # flag that could be used for view querysets
```

### Re-rendering variations
You might want to add new variations to a field. That means you need to render new variations for missing fields.
This can be accomplished using a management command.
```bash
python manage.py rendervariations 'app_name.model_name.field_name' [--replace] [-i/--ignore-missing]
```
The `replace` option will replace all existing files.
The `ignore-missing` option will suspend missing source file errors and keep
rendering variations for other files. Othervise command will stop on first
missing file.
