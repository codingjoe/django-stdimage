import os

from tests.test_models import TestStdImage

from . import forms, models


class TestStdImageField(TestStdImage):

    def test_save_form_data__new(self, db):
        instance = models.ThumbnailModel.objects.create(image=self.fixtures['100.gif'])
        org_path = instance.image.path
        assert os.path.exists(org_path)
        form = forms.ThumbnailModelForm(
            files=dict(image=self.fixtures['600x400.jpg']),
            instance=instance,
        )
        assert form.is_valid()
        obj = form.save()
        assert obj.image.name == 'img/600x400.jpg'
        assert os.path.exists(instance.image.path)
        assert not os.path.exists(org_path)

    def test_save_form_data__false(self, db):
        instance = models.ThumbnailModel.objects.create(image=self.fixtures['100.gif'])
        org_path = instance.image.path
        assert os.path.exists(org_path)
        form = forms.ThumbnailModelForm(
            data={'image-clear': '1'},
            instance=instance,
        )
        assert form.is_valid()
        obj = form.save()
        assert obj.image._file is None
        assert not os.path.exists(org_path)

    def test_save_form_data__none(self, db):
        instance = models.ThumbnailModel.objects.create(image=self.fixtures['100.gif'])
        org_path = instance.image.path
        assert os.path.exists(org_path)
        form = forms.ThumbnailModelForm(
            data={'image': None},
            instance=instance,
        )
        assert form.is_valid()
        obj = form.save()
        assert obj.image
        assert os.path.exists(org_path)
