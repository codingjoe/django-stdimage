from django.contrib import admin

from . import models

admin.site.register(models.AdminDeleteModel)
admin.site.register(models.AllModel)
admin.site.register(models.MultipleFieldsModel)
admin.site.register(models.ResizeCropModel)
admin.site.register(models.ResizeModel)
admin.site.register(models.SimpleModel)
admin.site.register(models.ThumbnailCropModel)
admin.site.register(models.ThumbnailModel)
