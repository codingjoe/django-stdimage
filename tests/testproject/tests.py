# coding: utf-8
from __future__ import absolute_import

import os
from django.conf import settings
from django.core.files import File
from django.test import TestCase
from django.contrib.auth.models import User

from .forms import *
from .models import NewParamsModel


IMG_DIR = os.path.join(settings.MEDIA_ROOT, 'img')


class TestStdImage(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('admin', 'admin@email.com',
                                             'admin')
        user.save()
        self.client.login(username='admin', password='admin')

        self.fixtures = {}
        fixtures_dir = os.path.join(settings.MEDIA_ROOT, 'fixtures')
        fixture_paths = os.listdir(fixtures_dir)
        for fixture_filename in fixture_paths:
            fixture_path = os.path.join(fixtures_dir, fixture_filename)
            if os.path.isfile(fixture_path):
                self.fixtures[fixture_filename] = File(open(fixture_path, 'rb'))

    def tearDown(self):
        """Close all open fixtures and delete everything from media"""
        for fixture in list(self.fixtures.values()):
            fixture.close()

        for root, dirs, files in os.walk(IMG_DIR, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


class TestModel(TestStdImage):
    """Tests model"""

    def test_simple(self):
        """Adds image and calls save."""
        instance = SimpleModel()
        instance.image = self.fixtures['100.gif']
        instance.save()
        self.assertEqual(SimpleModel.objects.count(), 1)
        self.assertEqual(SimpleModel.objects.get(pk=1), instance)
        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.gif')))

    def test_variations(self):
        """Adds image and checks filesystem as well as width and height."""
        instance = ResizeModel()
        instance.image = self.fixtures['600x400.jpg']
        instance.save()

        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.jpg')))
        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.thumbnail.jpg')))

        # smaller or similar size, must resolve to same file name
        # self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.medium.jpg')))

        self.assertEqual(instance.image.medium.width, 600)
        self.assertEqual(instance.image.medium.height, 400)

    def test_min_size(self):
        """Test if image matches minimal size requirements"""
        instance = AllModel()
        instance.image = self.fixtures['100.gif']
        instance.save()

        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.jpg')))


class TestModelForm(TestStdImage):
    """Tests ModelForm"""

    def test_min_size(self):
        """Test if image matches minimal size requirements"""
        form = ResizeCropModelForm({'image': self.fixtures['100.gif']})
        self.assertFalse(form.is_valid())

    def test_max_size(self):
        """Test if image matches maximal size requirements"""
        form = MaxSizeModelForm({'image': self.fixtures['600x400.jpg']})
        self.assertFalse(form.is_valid())


class TestAdmin(TestStdImage):
    """Tests admin"""

    def test_simple(self):
        """ Upload an image using the admin interface """
        self.client.post('/admin/testproject/simplemodel/add/', {
            'image': self.fixtures['100.gif']
        })
        self.assertEqual(SimpleModel.objects.count(), 1)

    def test_empty_fail(self):
        """ Will raise an validation error and will not add an intance """
        self.client.post('/admin/testproject/simplemodel/add/', {})
        self.assertEqual(SimpleModel.objects.count(), 0)

    def test_empty_success(self):
        """
        AdminDeleteModel has blank=True and will add an instance of the Model
        """
        self.client.post('/admin/testproject/admindeletemodel/add/', {})
        self.assertEqual(AdminDeleteModel.objects.count(), 1)

    def test_uploaded(self):
        """ Test simple upload """
        self.client.post('/admin/testproject/simplemodel/add/', {
            'image': self.fixtures['100.gif']
        })
        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.gif')))

    def test_delete(self):
        """ Test if an image can be deleted """

        self.client.post('/admin/testproject/admindeletemodel/add/', {
            'image': self.fixtures['100.gif']
        })
        #delete
        res = self.client.post('/admin/testproject/admindeletemodel/1/', {
            'image_delete': 'checked'
        })
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR,
                                                     'image.gif')))

    def test_thumbnail(self):
        """ Test if the thumbnail is there """

        self.client.post('/admin/testproject/thumbnailmodel/add/', {
            'image': self.fixtures['100.gif']
        })
        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.gif')))
        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.thumbnail.gif')))

    def test_delete_thumbnail(self):
        """ Delete an image with thumbnail """

        self.client.post('/admin/testproject/thumbnailmodel/add/', {
            'image': self.fixtures['100.gif']
        })

        #delete
        self.client.post('/admin/testproject/thumbnailmodel/1/', {
            'image_delete': 'checked'
        })
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.gif')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.thumbnail.gif')))

    def test_min_size(self):
        """ Tests if uploaded picture has minimal size """
        self.client.post('/admin/testproject/allmodel/add/', {
            'image': self.fixtures['100.gif']
        })
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.gif')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.thumbnail.gif')))

    def test_widget(self):
        """
        Tests the admin Widget
        """
        self.client.post('/admin/testproject/thumbnailmodel/add/', {
            'image': self.fixtures['600x400.jpg']
        })
        self.assertTrue(os.path.exists(os.path.join(IMG_DIR, 'image.admin.jpg')))

        response = self.client.get('/admin/testproject/thumbnailmodel/1/')
        self.assertContains(response, '<img src="/media/img/image.admin.jpg" alt="image thumbnail"/>')


class TestNewParams(TestStdImage):
    def test_new_params(self):
        """ Tests if uploaded picture has minimal size """
        self.client.post('/admin/testproject/newparamsmodel/add/', {
            'image': self.fixtures['600x400.jpg'],
            'image1': self.fixtures['600x400.jpg'],
            'image2': self.fixtures['600x400.jpg'],
        })
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.thumbnail.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.resized.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image.large.jpg')))

        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image1.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image1.thumbnail.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image1.resized.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image1.large.jpg')))

        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image2.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image2.thumbnail.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image2.resized.jpg')))
        self.assertFalse(os.path.exists(os.path.join(IMG_DIR, 'image2.large.jpg')))

        instance = NewParamsModel.objects.get(id=1)

        self.assertEquals(instance.image.thumbnail.width,  100)
        self.assertEquals(instance.image.thumbnail.height, 100)
        self.assertEquals(instance.image.resized.width,  300)
        self.assertEquals(instance.image.resized.height, 200)
        self.assertEquals(instance.image.large.width,  600)
        self.assertEquals(instance.image.large.height, 400)

        self.assertEquals(instance.image1.thumbnail.width,  100)
        self.assertEquals(instance.image1.thumbnail.height, 100)
        self.assertEquals(instance.image1.resized.width,  300)
        self.assertEquals(instance.image1.resized.height, 200)
        self.assertEquals(instance.image1.large.width,  600)
        self.assertEquals(instance.image1.large.height, 400)

        self.assertEquals(instance.image2.thumbnail.width,  100)
        self.assertEquals(instance.image2.thumbnail.height, 100)
        self.assertEquals(instance.image2.resized.width,  300)
        self.assertEquals(instance.image2.resized.height, 200)
        self.assertEquals(instance.image2.large.width,  600)
        self.assertEquals(instance.image2.large.height, 400)
