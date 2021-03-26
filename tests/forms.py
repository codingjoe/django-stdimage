from django import forms

from . import models


class ThumbnailModelForm(forms.ModelForm):
    class Meta:
        model = models.ThumbnailModel
        fields = "__all__"
