import os

import pytest
from PIL import Image

from stdimage.utils import UploadTo, render_variations
from tests.models import ManualVariationsModel
from tests.test_models import IMG_DIR


@pytest.mark.django_db
class TestRenderVariations:
    def test_render_variations(self, image_upload_file):
        instance = ManualVariationsModel.customer_manager.create(
            image=image_upload_file
        )
        path = os.path.join(IMG_DIR, 'image.thumbnail.jpg')
        assert not os.path.exists(path)
        render_variations(
            file_name=instance.image.name,
            variations={
                'thumbnail': {
                    'name': 'thumbnail',
                    'width': 150,
                    'height': 150,
                    'crop': True,
                    'resample': Image.ANTIALIAS
                }
            }
        )
        assert os.path.exists(path)


class TestUploadTo:
    def test_file_name(self):
        file_name = UploadTo()(object(), '/path/to/file.jpeg')
        assert file_name == '/path/to/file.jpeg'

    def test_file_name_lower(self):
        file_name = UploadTo()(object(), '/path/To/File.JPEG')
        assert file_name == '/path/to/file.jpeg'

    def test_file_name_no_ext(self):
        file_name = UploadTo()(object(), '/path/to/file')
        assert file_name == '/path/to/file'

    def test_file_name_kwargs(self):
        file_name = UploadTo(path='/foo', name='bar', ext='.BAZ')(
            object(), '/path/to/file')
        assert file_name == '/foo/bar.baz'

    def test_path_pattern(self):
        class U2(UploadTo):
            path_pattern = '/foo'

        file_name = U2()(
            object(), '/path/to/file.jpeg')
        assert file_name == '/foo/file.jpeg'

    def test_name_pattern(self):
        class U2(UploadTo):
            file_pattern = ".%(name)s%(ext)s"

        file_name = U2()(
            object(), '/path/to/file.jpeg')
        assert file_name == '/path/to/.file.jpeg'
