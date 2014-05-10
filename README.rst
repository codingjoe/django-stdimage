.. image:: https://travis-ci.org/codingjoe/django-stdimage.png
  :target: https://travis-ci.org/codingjoe/django-stdimage
.. image:: https://pypip.in/v/django-stdimage/badge.png
  :target: https://crate.io/packages/django-stdimage
.. image:: https://pypip.in/d/django-stdimage/badge.png
  :target: https://crate.io/packages/django-stdimage
.. image:: https://pypip.in/license/django-stdimage/badge.png
  :target: https://pypi.python.org/pypi/django-stdimage/

Django Standarized Image Field
==============================

Django Field that implement the following features:

* Django-Storages compatible (S3)
* Resize images to different sizes
* Access thumbnails on model level, no template tags required
* Preserves original image
* Restrict accepted image dimensions
* Allow image deletion
* Rename files to a standardized name (using a callable upload_to)

Installation
------------

Install latest PIL - there is really no reason to use this package without it

`easy_install django-stdimage`

or

`pip django-stdimage`

Put `'stdimage'` in the INSTALLED_APPS

Usage
-----
DISCLAIMER
This is another fork with another API architecture because the author
thinks that having 4 parameters in a tuple is confusing so he changed tuples into
dictionaries. The advantage is that you can specify any number of parameters.
Please note that in order to run on PyPy you need to keep disctionary keys the same
type. So please avoid mixing variation parameters as tuples and dictionaries.
END DISCLAIMER

Import it in your project, and use in your models.

Example::

    from stdimage import StdImageField
    from PIL import Image

    class MyClass(models.Model):
        ## works as ImageField
        image1 = StdImageField(upload_to='path/to/img')

        ## can be deleted through admin
        image2 = StdImageField(upload_to='path/to/img', blank=True)

        ## creates a thumbnail resized to maximum size to fit a 100x75 area
        # the original call
        image3 = StdImageField(upload_to='path/to/img', thumbnail_size=(100, 75))
        # is the same as intermediate-style call
        image3 = StdImageField(upload_to='path/to/img', variations={'thumbnail': (100, 75)})
        # is the same as the new-style-call
        image3 = StdImageField(upload_to='path/to/img', variations={'thumbnail': {"width": 100, "height": 75})

        ## creates a thumbnail resized to 100x100 croping if necessary
        image4 = StdImageField(upload_to='path/to/img', variations={'thumbnail': (100, 100, True)})
        # or the new style
        image4 = StdImageField(upload_to='path/to/img', variations={'thumbnail': {"width": 100, "height": 100, "crop":True}})

        ## creates a thumbnail resized to 100x100 croping if necessary and excepts only image greater than 1920x1080px
        ## if min_size is not specified, it won't accept smaller than the smallest variation image
        image5 = StdImageField(upload_to='path/to/img', variations={'thumbnail': (100, 100, True)}, min_size=(1920, 1080))

        ## Full ammo here. Please note all the definitions below are equal
        image_all = StdImageField(upload_to=upload_to, blank=True,
                               variations={'large': (600, 400), 'thumbnail': (100, 100, True), 'resized': (300, 200)})

        image_all = StdImageField(upload_to=upload_to, blank=True,
                               thumbnail_size=(100, 100, True),
                               variations={'large': {"width": 600, "height": 400}, 'resized': (300, 200)})

        image_all = StdImageField(upload_to=upload_to, blank=True,
                               thumbnail_size=(100, 100, True),
                               size=(300,200),
                               variations={'large': {"width": 600, "height": 400}})


For using generated thumbnail in templates use "myimagefield.thumbnail". Example::

    <a href="{{ object.myimage.url }}"><img alt="" src="{{ object.myimage.thumbnail.url }}"/></a>

About image names
-----------------

By default StdImageField stores images without modifying the file name. If you want to use more consistent file names you can use the build in upload functions.
Example::

    from stdimage import StdImageField, UPLOAD_TO_CLASS_NAME, UPLOAD_TO_CLASS_NAME_UUID, UPLOAD_TO_UUID
    from functools import partial

    class MyClass(models.Model)
        # Gets saved to MEDIA_ROOT/myclass/#FILENAME#.#EXT#
        image1 = StdImageField(upload_to=UPLOAD_TO_CLASS_NAME)

        # Gets saved to MEDIA_ROOT/myclass/pic.#EXT#
        image2 = StdImageField(upload_to=partial(UPLOAD_TO_CLASS_NAME, name='pic'))

        # Gets saved to MEDIA_ROOT/images/#UUID#.#EXT#
        image3 = StdImageField(upload_to=partial(UPLOAD_TO_UUID, path='images'))

        # Gets saved to MEDIA_ROOT/myclass/#UUID#.#EXT#
        image4 = StdImageField(upload_to=UPLOAD_TO_CLASS_NAME_UUID)


You can restrict the upload dimension of images using `min_size` and `max_size`. Both arguments accept a (width, height) tuple. By default, the minimum resolution is set to the biggest variation.
CAUTION: The `max_size` should be used with caution. As storage isn't expensive, you shouldn't restrict upload dimensions. If you seek prevent users form overflowing your memory you should restrict the HTTP upload body size.

.. image:: https://d2weczhvl823v0.cloudfront.net/codingjoe/django-stdimage/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free


Testing
-------
To run the tests please install the package using::

    python setup.py develop

So you can make changes. It's possible to install it directly with `python setup.py install` though.::
Then you can test by

    cd tests
    python manage.py test