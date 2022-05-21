[![version](https://img.shields.io/pypi/v/django-stdimage.svg)](https://pypi.python.org/pypi/django-stdimage/)
[![codecov](https://codecov.io/gh/codingjoe/django-stdimage/branch/master/graph/badge.svg)](https://codecov.io/gh/codingjoe/django-stdimage)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

# Django Standardized Image Field

This package has been deprecated in favor of [django-pictures][django-pictures].

## Migration Instructions

First, make sure you understand the differences between the two packages and
how to serve images in a modern web application via the [picture][picture-tag]-Element.

Next, follow the setup instructions for [django-pictures][django-pictures].

Once you are set up, change your models to use the new `PictureField` and provide the
 `aspect_ratios` you'd like to serve. Do create migrations just yet.

This step should be followed by changing your templates and frontend.
The new placeholders feature for local development should help you
to do this almost effortlessly.

Finally, run `makemigrations` and replace the `AlterField` operation with
`AlterPictureField`.

We highly recommend to use Django's `image_width` and `image_height` fields, to avoid
unnecessary IO. If you can add these fields to your model, you can use the following
snippet to populate them:

```python
import django.core.files.storage
from django.db import migrations, models
import pictures.models
from pictures.migrations import AlterPictureField

def forward(apps, schema_editor):
    for obj in apps.get_model("my-app.MyModel").objects.all().iterator():
        obj.image_width = obj.logo.width
        obj.image_height = obj.logo.height
        obj.save(update_fields=["image_height", "image_width"])

def backward(apps, schema_editor):
    apps.get_model("my-app.MyModel").objects.all().update(
        image_width=None,
        image_height=None,
    )

class Migration(migrations.Migration):
    dependencies = [
        ('my-app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name="mymodel",
            name="image_height",
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="mymodel",
            name="image_width",
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
        migrations.RunPython(forward, backward),
        AlterPictureField(
            model_name="mymodel",
            name="image",
            field=pictures.models.PictureField(
                aspect_ratios=["3/2", "3/1"],
                breakpoints={"desktop": 1024, "mobile": 576},
                container_width=1200,
                file_types=["WEBP"],
                grid_columns=12,
                height_field="image_height",
                pixel_densities=[1, 2],
                storage=django.core.files.storage.FileSystemStorage(),
                upload_to="pictures/",
                verbose_name="image",
                width_field="image_width",
            ),
        ),
    ]
```

[django-pictures]: https://github.com/codingjoe/django-pictures
[picture-tag]: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture

## Why would I want this?

This is a drop-in replacement for the [Django ImageField](https://docs.djangoproject.com/en/1.8/ref/models/fields/#django.db.models.ImageField) that provides a standardized way to handle image uploads.
It is designed to be as easy to use as possible, and to provide a consistent interface for all image fields.
It allows images to be presented in various size variants (eg:thumbnails, mid, and hi-res versions)
and it provides a way to handle images that are too large with validators.


## Features

Django Standardized Image Field implements the following features:

* [Django-Storages](https://django-storages.readthedocs.io/en/latest/) compatible (eg: S3, Azure, Google Cloud Storage, etc)
* Resizes images to different sizes
* Access thumbnails on model level, no template tags required
* Preserves original images
* Can be rendered asynchronously (ie as a [Celery job](https://realpython.com/asynchronous-tasks-with-django-and-celery/))
* Restricts acceptable image dimensions
* Renames a file to a standardized name format (using a callable `upload_to` function, see below)

## Installation

Simply install the latest stable package using the following command:

```bash
pip install django-stdimage
# or
pipenv install django-stdimage
```

and add `'stdimage'` to `INSTALLED_APP`s in your settings.py, that's it!

## Usage

Now it's instally you can use either: `StdImageField` or `JPEGField`.

`StdImageField` works just like Django's own
[ImageField](https://docs.djangoproject.com/en/dev/ref/models/fields/#imagefield)
except that you can specify different size variations.

The `JPEGField` is identical to the `StdImageField` but all images are
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

    # JPEGField variations are converted to JPEGs.
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

To use these variations in templates use `myimagefield.variation_name`.

Example:

```html
<a href="{{ object.myimage.url }}"><img alt="" src="{{ object.myimage.thumbnail.url }}"/></a>
```

### Upload to function

You can use a function for the `upload_to` argument. Using [Django Dynamic Filenames][dynamic_filenames].[dynamic_filenames]: https://github.com/codingjoe/django-dynamic-filenames

This allows images to be given unique paths and filenames based on the model instance.

Example

```python
from django.db import models
from stdimage import StdImageField
from dynamic_filenames import FilePattern

upload_to_pattern = FilePattern(
    filename_pattern='my_model/{app_label:.25}/{model_name:.30}/{uuid:base32}{ext}',
)


class MyModel(models.Model):
    # works just like django's ImageField
    image = StdImageField(upload_to=upload_to_pattern)
```

### Validators
The `StdImageField` doesn't implement any size validation out-of-the-box.
However, Validation can be specified using the validator attribute
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
orphaned files, should a file be deleted or replaced via a Django form and the object with
the `StdImageField` be deleted. It will not delete files if the field value is changed or
reassigned programatically. In these rare cases, you will need to handle proper deletion
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
to wait for your variations to be rendered in request, StdImage provides you the option to pass an
async keyword and a 'render_variations' function that triggers the async task.
Note that the callback is not transaction save, but the file variations will be present.
The example below is based on celery.

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
        upload_to='path/to/file/', # or use a function
        render_variations=image_processor  # pass boolean or callable
    )
    processed = models.BooleanField(default=False)  # flag that could be used for view querysets
```

### Re-rendering variations
You might have added or changed variations to an existing field. That means you will need to render new variations.
This can be accomplished using a management command.
```bash
python manage.py rendervariations 'app_name.model_name.field_name' [--replace] [-i/--ignore-missing]
```
The `replace` option will replace all existing files.
The `ignore-missing` option will suspend 'missing source file' errors and keep
rendering variations for other files. Otherwise, the command will stop on first missing file.
