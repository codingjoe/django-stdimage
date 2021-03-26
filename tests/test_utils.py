import os

import pytest
from PIL import Image

from stdimage.utils import render_variations
from tests.models import ManualVariationsModel
from tests.test_models import IMG_DIR


@pytest.mark.django_db
class TestRenderVariations:
    def test_render_variations(self, image_upload_file):
        instance = ManualVariationsModel.customer_manager.create(
            image=image_upload_file
        )
        path = os.path.join(IMG_DIR, "image.thumbnail.jpg")
        assert not os.path.exists(path)
        render_variations(
            file_name=instance.image.name,
            variations={
                "thumbnail": {
                    "name": "thumbnail",
                    "width": 150,
                    "height": 150,
                    "crop": True,
                    "resample": Image.ANTIALIAS,
                }
            },
        )
        assert os.path.exists(path)
