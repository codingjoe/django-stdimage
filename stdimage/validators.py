# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals)

from io import BytesIO
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.translation import ugettext_lazy as _


class BaseSizeValidator(BaseValidator):
    compare = lambda self, x: True

    def __init__(self, width, height):
        self.limit_value = width, height

    def __call__(self, value):
        cleaned = self.clean(value)
        params = {'with': self.limit_value[0], 'height': self.limit_value[1]}
        if self.compare(cleaned, self.limit_value):
            raise ValidationError(self.message, code=self.code, params=params)

    @staticmethod
    def clean(value):
        value.seek(0)
        stream = BytesIO(value.read())
        img = Image.open(stream)
        return img.size


class MaxSizeValidator(BaseSizeValidator):
    compare = lambda self, img_size, max_size:\
        img_size[0] > max_size[0] or img_size[1] > max_size[1]
    message = _('The image you uploaded is too large.'
                ' The required minimal resolution is:'
                ' %(with)sx%(height)s px.')
    code = 'max_resolution'


class MinSizeValidator(BaseSizeValidator):
    compare = lambda self, img_size, min_size:\
        img_size[0] < min_size[0] or img_size[1] < min_size[1]
    message = _('The image you uploaded is too small.'
                ' The required minimal resolution is:'
                ' %(with)sx%(height)s px.')
