from django.core.files.storage import default_storage

from .models import StdImageFieldFile


def render_variations(file_name, variations, replace=False,
                      storage=default_storage, field_class=StdImageFieldFile):
    """Render all variations for a given field."""
    for key, variation in variations.items():
        field_class.render_variation(
            file_name, variation, replace, storage
        )
