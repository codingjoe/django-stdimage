import logging
import os
import warnings
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import signals
from django.db.models.fields.files import (
    ImageField,
    ImageFieldFile,
    ImageFileDescriptor,
)
from PIL import Image, ImageFile, ImageOps
from PIL.Image import Resampling

from .validators import MinSizeValidator

logger = logging.getLogger()


warnings.warn(
    "The django-stdimage is deprecated in favor of django-pictures.\n"
    "Migration instructions are available in the README:\n"
    "https://github.com/codingjoe/django-stdimage#migration-instructions",
    DeprecationWarning,
)


class StdImageFileDescriptor(ImageFileDescriptor):
    """The variation property of the field is accessible in instance cases."""

    def __set__(self, instance, value):
        super().__set__(instance, value)
        self.field.set_variations(instance)


class StdImageFieldFile(ImageFieldFile):
    """Like ImageFieldFile but handles variations."""

    def save(self, name, content, save=True):
        super().save(name, content, save)
        render_variations = self.field.render_variations
        if callable(render_variations):
            render_variations = render_variations(
                file_name=self.name,
                variations=self.field.variations,
                storage=self.storage,
            )
        if not isinstance(render_variations, bool):
            msg = (
                '"render_variations" callable expects a boolean return value,'
                " but got %s"
            ) % type(render_variations)
            raise TypeError(msg)
        if render_variations:
            self.render_variations()

    @staticmethod
    def is_smaller(img, variation):
        return img.size[0] > variation["width"] or img.size[1] > variation["height"]

    def render_variations(self, replace=True):
        """Render all image variations and saves them to the storage."""
        for _, variation in self.field.variations.items():
            self.render_variation(self.name, variation, replace, self.storage)

    @classmethod
    def render_variation(
        cls, file_name, variation, replace=True, storage=default_storage
    ):
        """Render an image variation and saves it to the storage."""
        variation_name = cls.get_variation_name(file_name, variation["name"])
        file_overwrite = getattr(storage, "file_overwrite", False)
        if not replace and storage.exists(variation_name):
            logger.info('File "%s" already exists.', variation_name)
            return variation_name
        elif replace and not file_overwrite and storage.exists(variation_name):
            logger.warning(
                'File "%s" already exists and will be overwritten.', variation_name
            )
            storage.delete(variation_name)

        ImageFile.LOAD_TRUNCATED_IMAGES = True
        with storage.open(file_name) as f:
            with Image.open(f) as img:
                img, save_kargs = cls.process_variation(variation, image=img)
                with BytesIO() as file_buffer:
                    img.save(file_buffer, **save_kargs)
                    f = ContentFile(file_buffer.getvalue())
                    storage.save(variation_name, f)
        return variation_name

    @classmethod
    def process_variation(cls, variation, image):
        """Process variation before actual saving."""
        save_kargs = {}
        file_format = image.format
        save_kargs["format"] = file_format

        resample = variation["resample"]

        if cls.is_smaller(image, variation):
            factor = 1
            while (
                image.size[0] / factor > 2 * variation["width"]
                and image.size[1] * 2 / factor > 2 * variation["height"]
            ):
                factor *= 2
            if factor > 1:
                image.thumbnail(
                    (int(image.size[0] / factor), int(image.size[1] / factor)),
                    resample=resample,
                )

            size = variation["width"], variation["height"]
            size = tuple(int(i) if i is not None else i for i in size)

            if file_format == "JPEG":
                # http://stackoverflow.com/a/21669827
                image = image.convert("RGB")
                save_kargs["optimize"] = True
                save_kargs["quality"] = "web_high"
                if size[0] * size[1] > 10000:  # roughly <10kb
                    save_kargs["progressive"] = True

            if variation["crop"]:
                image = ImageOps.fit(image, size, method=resample)
            else:
                image.thumbnail(size, resample=resample)

        return image, save_kargs

    @classmethod
    def get_variation_name(cls, file_name, variation_name):
        """Return the variation file name based on the variation."""
        path, ext = os.path.splitext(file_name)
        path, file_name = os.path.split(path)
        file_name = "{file_name}.{variation_name}{extension}".format(
            **{
                "file_name": file_name,
                "variation_name": variation_name,
                "extension": ext,
            }
        )
        return os.path.join(path, file_name)

    def delete(self, save=True):
        self.delete_variations()
        super().delete(save)

    def delete_variations(self):
        for variation in self.field.variations:
            variation_name = self.get_variation_name(self.name, variation)
            self.storage.delete(variation_name)

    def __getstate__(self):
        state = super().__getstate__()
        state["variations"] = {}
        for variation_name in self.field.variations:
            if variation := getattr(self, variation_name, None):
                variation_state = variation.__getstate__()
                state["variations"][variation_name] = variation_state
        return state

    def __setstate__(self, state):
        variations = state["variations"]
        state.pop("variations")
        super().__setstate__(state)
        for key, value in variations.items():
            cls = ImageFieldFile
            field = cls.__new__(cls)
            setattr(self, key, field)
            getattr(self, key).__setstate__(value)


class StdImageField(ImageField):
    """
    Django ImageField that is able to create different size variations.

    Extra features are:

    -   Django-Storages compatible (S3)
    -   Access thumbnails on model level, no template tags required
    -   Preserves original image
    -   Asynchronous rendering (Celery & Co)
    -   Multi threading and processing for optimum performance
    -   Restrict accepted image dimensions
    -   Rename files to a standardized name (using a callable upload_to)

    """

    descriptor_class = StdImageFileDescriptor
    attr_class = StdImageFieldFile
    def_variation = {
        "width": None,
        "height": None,
        "crop": False,
        "resample": Resampling.LANCZOS,
    }

    def __init__(
        self,
        verbose_name=None,
        name=None,
        variations=None,
        render_variations=True,
        force_min_size=False,
        delete_orphans=False,
        **kwargs,
    ):
        """
        Standardized ImageField for Django.

        Usage::

            StdImageField(
                upload_to='PATH',
                variations={
                    'thumbnail': {"width", "height", "crop", "resample"},
                },
                delete_orphans=True,
            )

        Args:
            variations (dict):
                Different size variations of the image.
            render_variations (bool, callable):
                Boolean or callable that returns a boolean. If True, the built-in
                image render will be used. The callable gets passed the ``app_name``,
                ``model``, ``field_name`` and ``pk``. Default: ``True``
            delete_orphans (bool):
                If ``True``, files orphaned files will be removed in case a new file
                is assigned or the field is cleared. This will only remove work for
                Django forms. If you unassign or reassign a field in code, you will
                need to remove the orphaned files yourself.

        """
        if not variations:
            variations = {}
        if not isinstance(variations, dict):
            msg = ('"variations" expects a dict,' " but got %s") % type(variations)
            raise TypeError(msg)
        if not (isinstance(render_variations, bool) or callable(render_variations)):
            msg = (
                '"render_variations" excepts a boolean or callable,' " but got %s"
            ) % type(render_variations)
            raise TypeError(msg)

        self._variations = variations
        self.force_min_size = force_min_size
        self.render_variations = render_variations
        self.variations = {}
        self.delete_orphans = delete_orphans

        for nm, prm in list(variations.items()):
            self.add_variation(nm, prm)

        if self.variations and self.force_min_size:
            self.min_size = (
                max(self.variations.values(), key=lambda x: x["width"])["width"],
                max(self.variations.values(), key=lambda x: x["height"])["height"],
            )

        super().__init__(verbose_name=verbose_name, name=name, **kwargs)

        # The attribute name of the old file to use on the model object
        self._old_attname = "_old_%s" % name

    def add_variation(self, name, params):
        variation = self.def_variation.copy()
        variation["kwargs"] = {}
        if isinstance(params, (list, tuple)):
            variation.update(dict(zip(("width", "height", "crop", "kwargs"), params)))
        else:
            variation.update(params)
        variation["name"] = name
        self.variations[name] = variation

    def set_variations(self, instance=None, **kwargs):
        """
        Create a "variation" object as attribute of the ImageField instance.

        Variation attribute will be of the same class as the original image, so
        "path", "url"... properties can be used

        :param instance: FileField
        """
        deferred_field = self.name in instance.get_deferred_fields()
        if not deferred_field and getattr(instance, self.name):
            field = getattr(instance, self.name)
            if field._committed:
                for name, variation in list(self.variations.items()):
                    variation_name = self.attr_class.get_variation_name(
                        field.name, variation["name"]
                    )
                    variation_field = ImageFieldFile(instance, self, variation_name)
                    setattr(field, name, variation_field)

    def post_delete_callback(self, sender, instance, **kwargs):
        getattr(instance, self.name).delete(False)

    def contribute_to_class(self, cls, name):
        """Generate all operations on specified signals."""
        super().contribute_to_class(cls, name)
        signals.post_init.connect(self.set_variations, sender=cls)
        if self.delete_orphans:
            signals.post_delete.connect(self.post_delete_callback, sender=cls)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if self.force_min_size:
            MinSizeValidator(self.min_size[0], self.min_size[1])(value)

    def save_form_data(self, instance, data):
        if self.delete_orphans and (data is False or data is not None):
            file = getattr(instance, self.name)
            if file and file._committed and file != data:
                # Store the old file which should be deleted if the new one is valid
                setattr(instance, self._old_attname, file)
        super().save_form_data(instance, data)

    def pre_save(self, model_instance, add):
        if hasattr(model_instance, self._old_attname):
            # Delete the old file and its variations from the storage
            old_file = getattr(model_instance, self._old_attname)
            old_file.delete_variations()
            old_file.storage.delete(old_file.name)
            delattr(model_instance, self._old_attname)
        return super().pre_save(model_instance, add)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return (
            name,
            path,
            args,
            {
                **kwargs,
                "variations": self._variations,
                "force_min_size": self.force_min_size,
            },
        )


class JPEGFieldFile(StdImageFieldFile):
    @classmethod
    def get_variation_name(cls, file_name, variation_name):
        path = super().get_variation_name(file_name, variation_name)
        path, ext = os.path.splitext(path)
        return "%s.jpeg" % path

    @classmethod
    def process_variation(cls, variation, image):
        """Process variation before actual saving."""
        save_kargs = {}
        file_format = "JPEG"
        save_kargs["format"] = file_format

        resample = variation["resample"]

        width = image.size[0] if variation["width"] is None else variation["width"]
        height = image.size[1] if variation["height"] is None else variation["height"]

        factor = 1
        while (
            image.size[0] / factor > 2 * width
            and image.size[1] * 2 / factor > 2 * height
        ):
            factor *= 2
        if factor > 1:
            image.thumbnail(
                (int(image.size[0] / factor), int(image.size[1] / factor)),
                resample=resample,
            )

        size = width, height
        size = tuple(int(i) if i is not None else i for i in size)

        # http://stackoverflow.com/a/21669827
        image = image.convert("RGB")
        save_kargs["optimize"] = True
        save_kargs["quality"] = "web_high"
        if size[0] * size[1] > 10000:  # roughly <10kb
            save_kargs["progressive"] = True

        if variation["crop"]:
            image = ImageOps.fit(image, size, method=resample)
        else:
            image.thumbnail(size, resample=resample)

        save_kargs.update(variation["kwargs"])

        return image, save_kargs


class JPEGField(StdImageField):
    attr_class = JPEGFieldFile
