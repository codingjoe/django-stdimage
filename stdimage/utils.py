from django.core.files.storage import default_storage

from .models import StdImageField, StdImageFieldFile


def pre_delete_delete_callback(sender, instance, **kwargs):
    for field in instance._meta.fields:
        if isinstance(field, StdImageField):
            getattr(instance, field.name).delete(False)


def pre_save_delete_callback(sender, instance, **kwargs):
    if instance.pk:
        obj = sender.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            if isinstance(field, StdImageField):
                obj_field = getattr(obj, field.name)
                instance_field = getattr(instance, field.name)
                if obj_field and obj_field != instance_field:
                    obj_field.delete(False)


def render_variations(file_name, variations, replace=False,
                      storage=default_storage, field_class=StdImageFieldFile):
    """Render all variations for a given field."""
    for key, variation in variations.items():
        field_class.render_variation(
            file_name, variation, replace, storage
        )
