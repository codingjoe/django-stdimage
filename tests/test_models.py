# coding: utf-8
from __future__ import absolute_import, unicode_literals

import filecmp
import os
import shutil
import uuid


class UUID4Monkey(object):
    hex = '653d1c6863404b9689b75fa930c9d0a0'


uuid.__dict__['uuid4'] = lambda: UUID4Monkey()

import django  # NoQA
from django.conf import settings  # NoQA
from django.core.files import File  # NoQA
from django.test import TestCase  # NoQA
from django.contrib.auth.models import User  # NoQA

from .models import (
    SimpleModel, ResizeModel, AdminDeleteModel,
    ThumbnailModel, ResizeCropModel, AutoSlugClassNameDirModel,
    UUIDModel,
    UtilVariationsModel,
    ThumbnailWithoutDirectoryModel,
    CustomRenderVariationsModel, ProgressiveJpegModel)  # NoQA

IMG_DIR = os.path.join(settings.MEDIA_ROOT, 'img')

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'fixtures'
)


class TestStdImage(TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'admin@email.com', 'admin')
        self.client.login(username='admin', password='admin')

        self.fixtures = {}
        fixture_paths = os.listdir(FIXTURE_DIR)
        for fixture_filename in fixture_paths:
            fixture_path = os.path.join(FIXTURE_DIR, fixture_filename)
            if os.path.isfile(fixture_path):
                f = open(fixture_path, 'rb')
                self.fixtures[fixture_filename] = File(f)

    def tearDown(self):
        """Close all open fixtures and delete everything from media"""
        for fixture in list(self.fixtures.values()):
            fixture.close()

        for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


class TestModel(TestStdImage):
    """Tests StdImage ModelField"""

    def test_simple(self):
        """Tests if Field behaves just like Django's ImageField."""
        instance = SimpleModel.objects.create(image=self.fixtures['100.gif'])
        target_file = os.path.join(IMG_DIR, '100.gif')
        source_file = os.path.join(FIXTURE_DIR, '100.gif')

        self.assertEqual(SimpleModel.objects.count(), 1)
        self.assertEqual(SimpleModel.objects.get(pk=1), instance)

        self.assertTrue(os.path.exists(target_file))

        self.assertTrue(filecmp.cmp(source_file, target_file))

    def test_variations(self):
        """Adds image and checks filesystem as well as width and height."""
        instance = ResizeModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )

        source_file = os.path.join(FIXTURE_DIR, '600x400.jpg')

        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.jpg')))
        self.assertEqual(instance.image.width, 600)
        self.assertEqual(instance.image.height, 400)
        path = os.path.join(IMG_DIR, 'image.jpg')
        assert filecmp.cmp(source_file, path)

        path = os.path.join(IMG_DIR, 'image.medium.jpg')
        assert os.path.exists(path)
        self.assertEqual(instance.image.medium.width, 400)
        self.assertLessEqual(instance.image.medium.height, 400)
        self.assertFalse(filecmp.cmp(
            source_file,
            os.path.join(IMG_DIR, 'image.medium.jpg')))

        self.assertTrue(os.path.exists(
            os.path.join(IMG_DIR, 'image.thumbnail.jpg'))
        )
        self.assertEqual(instance.image.thumbnail.width, 100)
        self.assertLessEqual(instance.image.thumbnail.height, 75)
        self.assertFalse(filecmp.cmp(
            source_file,
            os.path.join(IMG_DIR, 'image.thumbnail.jpg'))
        )

    def test_cropping(self):
        instance = ResizeCropModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        self.assertEqual(instance.image.thumbnail.width, 150)
        self.assertEqual(instance.image.thumbnail.height, 150)

    def test_variations_override(self):
        source_file = os.path.join(FIXTURE_DIR, '600x400.jpg')
        target_file = os.path.join(IMG_DIR, 'image.thumbnail.jpg')
        os.mkdir(IMG_DIR)
        shutil.copyfile(source_file, target_file)
        ResizeModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        thumbnail_path = os.path.join(IMG_DIR, 'image.thumbnail.jpg')
        assert os.path.exists(thumbnail_path)
        thumbnail_path = os.path.join(IMG_DIR, 'image.thumbnail_1.jpg')
        assert not os.path.exists(thumbnail_path)

    def test_delete_thumbnail(self):
        """Delete an image with thumbnail"""
        obj = ThumbnailModel.objects.create(
            image=self.fixtures['100.gif']
        )
        obj.image.delete()
        path = os.path.join(IMG_DIR, 'image.gif')
        assert not os.path.exists(path)

        path = os.path.join(IMG_DIR, 'image.thumbnail.gif')
        assert not os.path.exists(path)

    def test_force_min_size(self):
        self.client.post('/admin/tests/forceminsizemodel/add/', {
            'image': self.fixtures['100.gif'],
        })
        path = os.path.join(IMG_DIR, 'image.gif')
        assert not os.path.exists(path)

    def test_progressive_jpeg_from_jpeg(self):
        ProgressiveJpegModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        progressive_path = os.path.join(IMG_DIR, 'image.progressive.jpg')
        assert os.path.exists(progressive_path)

    def test_progressive_jpeg_from_png(self):
        ProgressiveJpegModel.objects.create(
            image=self.fixtures['600x400.png']
        )
        progressive_path = os.path.join(IMG_DIR, 'image.progressive.jpg')
        assert os.path.exists(progressive_path)

        progressive_path = os.path.join(IMG_DIR, 'image.progressive.png')
        assert not os.path.exists(progressive_path)

    def test_progressive_jpeg_from_gif(self):
        ProgressiveJpegModel.objects.create(
            image=self.fixtures['600x400.gif']
        )
        progressive_path = os.path.join(IMG_DIR, 'image.progressive.jpg')
        assert os.path.exists(progressive_path)

        progressive_path = os.path.join(IMG_DIR, 'image.progressive.gif')
        assert not os.path.exists(progressive_path)

    def test_thumbnail_save_without_directory(self):
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

    def test_custom_render_variations(self):
        instance = CustomRenderVariationsModel.objects.create(
            image=self.fixtures['600x400.jpg']
        )
        # Image size must be 100x100 despite variations settings
        assert instance.image.thumbnail.width == 100
        assert instance.image.thumbnail.height == 100


class TestUtils(TestStdImage):
    """Tests Utils"""

    def test_deletion_singnal_receiver(self):
        obj = SimpleModel.objects.create(
            image=self.fixtures['100.gif']
        )
        obj.delete()
        self.assertFalse(
            os.path.exists(os.path.join(IMG_DIR, 'image.gif'))
        )

    def test_pre_save_delete_callback_clear(self):
        AdminDeleteModel.objects.create(
            image=self.fixtures['100.gif']
        )
        if django.VERSION >= (1, 9):
            self.client.post('/admin/tests/admindeletemodel/1/change/', {
                'image-clear': 'checked',
            })
        else:
            self.client.post('/admin/tests/admindeletemodel/1/', {
                'image-clear': 'checked',
            })
        self.assertFalse(
            os.path.exists(os.path.join(IMG_DIR, 'image.gif'))
        )

    def test_pre_save_delete_callback_new(self):
        AdminDeleteModel.objects.create(
            image=self.fixtures['100.gif']
        )
        if django.VERSION >= (1, 9):
            self.client.post('/admin/tests/admindeletemodel/1/change/', {
                'image': self.fixtures['600x400.jpg'],
            })
        else:
            self.client.post('/admin/tests/admindeletemodel/1/', {
                'image': self.fixtures['600x400.jpg'],
            })
        self.assertFalse(
            os.path.exists(os.path.join(IMG_DIR, 'image.gif'))
        )

    def test_upload_to_auto_slug_class_name_dir(self):
        AutoSlugClassNameDirModel.objects.create(
            name='foo bar',
            image=self.fixtures['100.gif']
        )
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            'autoslugclassnamedirmodel',
            'foo-bar.gif'
        )
        self.assertTrue(os.path.exists(file_path))

    def test_upload_to_uuid(self):
        UUIDModel.objects.create(image=self.fixtures['100.gif'])
        file_path = os.path.join(
            IMG_DIR,
            '653d1c6863404b9689b75fa930c9d0a0.gif'
        )
        self.assertTrue(os.path.exists(file_path))

    def test_render_variations_callback(self):
        UtilVariationsModel.objects.create(image=self.fixtures['100.gif'])
        file_path = os.path.join(
            IMG_DIR,
            'image.thumbnail.gif'
        )
        self.assertTrue(os.path.exists(file_path))


class TestValidators(TestStdImage):
    def test_max_size_validator(self):
        self.client.post('/admin/tests/maxsizemodel/add/', {
            'image': self.fixtures['600x400.jpg'],
        })
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.jpg')))

    def test_min_size_validator(self):
        self.client.post('/admin/tests/minsizemodel/add/', {
            'image': self.fixtures['100.gif'],
        })
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.gif')))
