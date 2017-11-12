import hashlib
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.management import CommandError, call_command

from tests.models import (
    CustomRenderVariationsModel, MyStorageModel, ThumbnailModel
)


@pytest.mark.django_db
class TestRenderVariations:

    @pytest.fixture(autouse=True)
    def _swap_concurrent_executor(self, monkeypatch):
        """Use ThreadPoolExecutor for coverage reports."""
        monkeypatch.setattr(
            'concurrent.futures.ProcessPoolExecutor',
            ThreadPoolExecutor,
        )

    def test_no_options(self, image_upload_file):
        obj = ThumbnailModel.objects.create(
            image=image_upload_file
        )
        file_path = obj.image.thumbnail.path
        obj.image.delete_variations()
        call_command(
            'rendervariations',
            'tests.ThumbnailModel.image'
        )
        assert os.path.exists(file_path)

    def test_multiprocessing(self, image_upload_file):
        objs = [
            ThumbnailModel.objects.create(
                image=image_upload_file
            )
            for _ in range(100)
        ]
        file_names = [
            obj.image.thumbnail.path
            for obj in objs
            ]
        for obj in objs:
            obj.image.delete_variations()
        assert not any([os.path.exists(f) for f in file_names])
        call_command(
            'rendervariations',
            'tests.ThumbnailModel.image'
        )
        assert any([os.path.exists(f) for f in file_names])

    def test_no_replace(self, image_upload_file):
        obj = ThumbnailModel.objects.create(image=image_upload_file)
        file_path = obj.image.thumbnail.path
        assert os.path.exists(file_path)
        before = os.path.getmtime(file_path)
        time.sleep(1)
        call_command(
            'rendervariations',
            'tests.ThumbnailModel.image',
        )
        assert os.path.exists(file_path)
        after = os.path.getmtime(file_path)
        assert before == after

    def test_replace(self, image_upload_file):
        obj = ThumbnailModel.objects.create(image=image_upload_file)
        file_path = obj.image.thumbnail.path
        assert os.path.exists(file_path)
        before = os.path.getmtime(file_path)
        time.sleep(1)
        call_command(
            'rendervariations',
            'tests.ThumbnailModel.image',
            replace=True
        )
        assert os.path.exists(file_path)
        after = os.path.getmtime(file_path)
        assert before != after

    def test_none_default_storage(self, image_upload_file):
        obj = MyStorageModel.customer_manager.create(
            image=image_upload_file
        )
        file_path = obj.image.thumbnail.path
        obj.image.delete_variations()
        call_command(
            'rendervariations',
            'tests.MyStorageModel.image'
        )
        assert os.path.exists(file_path)

    def test_invalid_field_path(self):
        with pytest.raises(CommandError) as exc_info:
            call_command(
                'rendervariations',
                'MyStorageModel.image'
            )

        error_message = "Error parsing field_path 'MyStorageModel.image'. "\
                        "Use format <app.model.field app.model.field>."
        assert str(exc_info.value) == error_message

    def test_custom_render_variations(self, image_upload_file):
        obj = CustomRenderVariationsModel.objects.create(
            image=image_upload_file
        )
        file_path = obj.image.thumbnail.path
        assert os.path.exists(file_path)
        with open(file_path, 'rb') as f:
            before = hashlib.md5(f.read()).hexdigest()
        call_command(
            'rendervariations',
            'tests.CustomRenderVariationsModel.image',
            replace=True,
        )
        assert os.path.exists(file_path)
        with open(file_path, 'rb') as f:
            after = hashlib.md5(f.read()).hexdigest()
        assert before == after
