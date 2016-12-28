import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


@pytest.fixture
def imagedata():
    img = Image.new('RGB', (250, 250), (255, 55, 255))

    output = io.BytesIO()
    img.save(output, format='JPEG')

    return output


@pytest.fixture
def image_upload_file(imagedata):
    return SimpleUploadedFile(
        'testfile.jpg',
        imagedata.getvalue()
    )
