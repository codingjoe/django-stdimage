import io
import os
import time

import pytest
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from . import models
from .models import (AdminDeleteModel, CustomRenderVariationsModel, ResizeCropModel,
                     ResizeModel, SimpleModel, ThumbnailModel,
                     ThumbnailWithoutDirectoryModel, UtilVariationsModel,)

IMG_DIR = os.path.join(settings.MEDIA_ROOT, 'img')

FIXTURES = [
    ('100.gif', 'GIF', 100, 100),
    ('600x400.gif', 'GIF', 600, 400),
    ('600x400.jpg', 'JPEG', 600, 400),
    ('600x400.jpg', 'PNG', 600, 400),
]


class TestStdImage:
    fixtures = {}

    @pytest.fixture(autouse=True)
    def setup(self):
        for fixture_filename, img_format, width, height in FIXTURES:
            with io.BytesIO() as f:
                img = Image.new('RGB', (width, height), (255, 55, 255))
                img.save(f, format=img_format)
                suf = SimpleUploadedFile(fixture_filename, f.getvalue())
                self.fixtures[fixture_filename] = suf

        yield

        for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


class TestModel(TestStdImage):
    """Tests StdImage ModelField"""

    def test_simple(self, db):
        """Tests if Field behaves just like Django's ImageField."""
        instance = SimpleModel.objects.create(image=self.fixtures['100.gif'])
        target_file = os.path.join(IMG_DIR, '100.gif')
        source_file = self.fixtures['100.gif']

        assert SimpleModel.objects.count() == 1
        assert SimpleModel.objects.get(pk=1) == instance

        assert os.path.exists(target_file)

        with open(target_file, 'rb') as f:
            source_file.seek(0)
            assert source_file.read() == f.read()

    def test_variations(self, db):
        """Adds image and checks filesystem as well as width and height."""
        instance = ResizeModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )

        source_file = self.fixtures['600x400.jpg']

        assert os.path.exists(os.path.join(IMG_DIR, '600x400.jpg'))
        assert instance.image.width == 600
        assert instance.image.height == 400
        path = os.path.join(IMG_DIR, '600x400.jpg')

        with open(path, 'rb') as f:
            source_file.seek(0)
            assert source_file.read() == f.read()

        path = os.path.join(IMG_DIR, '600x400.medium.jpg')
        assert os.path.exists(path)
        assert instance.image.medium.width == 400
        assert instance.image.medium.height <= 400
        with open(os.path.join(IMG_DIR, '600x400.medium.jpg'), 'rb') as f:
            source_file.seek(0)
            assert source_file.read() != f.read()

        assert os.path.exists(os.path.join(IMG_DIR, '600x400.thumbnail.jpg'))
        assert instance.image.thumbnail.width == 100
        assert instance.image.thumbnail.height <= 75
        with open(os.path.join(IMG_DIR, '600x400.thumbnail.jpg'), 'rb') as f:
            source_file.seek(0)
            assert source_file.read() != f.read()

    def test_cropping(self, db):
        instance = ResizeCropModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        assert instance.image.thumbnail.width == 150
        assert instance.image.thumbnail.height == 150

    def test_variations_override(self, db):
        source_file = self.fixtures['600x400.jpg']
        target_file = os.path.join(IMG_DIR, 'image.thumbnail.jpg')
        os.mkdir(IMG_DIR)
        default_storage.save(target_file, source_file)
        ResizeModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        thumbnail_path = os.path.join(IMG_DIR, 'image.thumbnail.jpg')
        assert os.path.exists(thumbnail_path)
        thumbnail_path = os.path.join(IMG_DIR, 'image.thumbnail_1.jpg')
        assert not os.path.exists(thumbnail_path)

    def test_delete_thumbnail(self, db):
        """Delete an image with thumbnail"""
        obj = ThumbnailModel.objects.create(
            image=self.fixtures['100.gif']
        )
        obj.image.delete()
        path = os.path.join(IMG_DIR, 'image.gif')
        assert not os.path.exists(path)

        path = os.path.join(IMG_DIR, 'image.thumbnail.gif')
        assert not os.path.exists(path)

    def test_fore_min_size(self, admin_client):
        admin_client.post('/admin/tests/forceminsizemodel/add/', {
            'image': self.fixtures['100.gif'],
        })
        path = os.path.join(IMG_DIR, 'image.gif')
        assert not os.path.exists(path)

    def test_thumbnail_save_without_directory(self, db):
        obj = ThumbnailWithoutDirectoryModel.objects.create(
            image=self.fixtures['100.gif']
        )
        obj.save()
        # Our model saves the images directly into the MEDIA_ROOT directory
        # not IMG_DIR, under a custom name
        original = os.path.join(settings.MEDIA_ROOT, 'custom.gif')
        thumbnail = os.path.join(settings.MEDIA_ROOT, 'custom.thumbnail.gif')
        assert os.path.exists(original)
        assert os.path.exists(thumbnail)

    def test_custom_render_variations(self, db):
        instance = CustomRenderVariationsModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        # Image size must be 100x100 despite variations settings
        assert instance.image.thumbnail.width == 100
        assert instance.image.thumbnail.height == 100

    def test_defer(self, db, django_assert_num_queries):
        """
        `set_variations` does not access a deferred field.

        Accessing a deferred field would cause Django to do
        a second implicit database query.
        """
        instance = ResizeModel.objects.create(image=self.fixtures['100.gif'])
        with django_assert_num_queries(1):
            deferred = ResizeModel.objects.only('pk').get(pk=instance.pk)
        with django_assert_num_queries(1):
            deferred.image
        assert instance.image.thumbnail == deferred.image.thumbnail


class TestUtils(TestStdImage):
    """Tests Utils"""

    def test_deletion_singnal_receiver(self, db):
        obj = AdminDeleteModel.objects.create(
            image=self.fixtures['100.gif']
        )
        path = obj.image.path
        obj.delete()
        assert not os.path.exists(path)

    def test_deletion_singnal_receiver_many(self, db):
        obj = AdminDeleteModel.objects.create(
            image=self.fixtures['100.gif']
        )
        path = obj.image.path
        AdminDeleteModel.objects.all().delete()
        assert not os.path.exists(path)

    def test_pre_save_delete_callback_clear(self, admin_client):
        obj = AdminDeleteModel.objects.create(
            image=self.fixtures['100.gif']
        )
        path = obj.image.path
        admin_client.post('/admin/tests/admindeletemodel/1/change/', {
            'image-clear': 'checked',
        })
        assert not os.path.exists(path)

    def test_pre_save_delete_callback_new(self, admin_client):
        AdminDeleteModel.objects.create(
            image=self.fixtures['100.gif']
        )
        admin_client.post('/admin/tests/admindeletemodel/1/change/', {
            'image': self.fixtures['600x400.jpg'],
        })
        assert not os.path.exists(os.path.join(IMG_DIR, 'image.gif'))

    def test_render_variations_callback(self, db):
        obj = UtilVariationsModel.objects.create(image=self.fixtures['100.gif'])
        file_path = obj.image.thumbnail.path
        assert os.path.exists(file_path)

    def test_render_variations_overwrite(self, db, image_upload_file):
        obj = ThumbnailModel.objects.create(image=image_upload_file)
        file_path = obj.image.thumbnail.path
        before = os.path.getmtime(file_path)
        time.sleep(0.1)
        os.remove(obj.image.path)
        assert os.path.exists(file_path)
        obj.image = image_upload_file
        obj.save()
        assert file_path == obj.image.thumbnail.path
        after = os.path.getmtime(file_path)
        assert before != after, obj.image.path


class TestValidators(TestStdImage):
    def test_max_size_validator(self, admin_client):
        response = admin_client.post('/admin/tests/maxsizemodel/add/', {
            'image': self.fixtures['600x400.jpg'],
        })
        assert 'too large' in response.context['adminform'].form.errors['image'][0]
        assert not os.path.exists(os.path.join(IMG_DIR, '800x600.jpg'))

    def test_min_size_validator(self, admin_client):
        response = admin_client.post('/admin/tests/minsizemodel/add/', {
            'image': self.fixtures['100.gif'],
        })
        assert 'too small' in response.context['adminform'].form.errors['image'][0]
        assert not os.path.exists(os.path.join(IMG_DIR, '100.gif'))


class TestJPEGField(TestStdImage):
    def test_convert(self, db):
        obj = models.JPEGModel.objects.create(image=self.fixtures['100.gif'])
        assert obj.image.thumbnail.path.endswith('img/100.thumbnail.jpeg')
        assert obj.image.full.width == 100
        assert obj.image.full.height == 100
