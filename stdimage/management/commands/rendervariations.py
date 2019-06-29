from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

import progressbar
from django.apps import apps
from django.core.files.storage import get_storage_class
from django.core.management import BaseCommand, CommandError

from stdimage.utils import render_variations


class Command(BaseCommand):
    help = 'Renders all variations of a StdImageField.'
    args = '<app.model.field app.model.field>'

    def add_arguments(self, parser):
        parser.add_argument('field_path',
                            nargs='+',
                            type=str,
                            help='<app.model.field app.model.field>')
        parser.add_argument('--replace',
                            action='store_true',
                            dest='replace',
                            default=False,
                            help='Replace existing files.')

        parser.add_argument('-i', '--ignore-missing',
                            action='store_true',
                            dest='ignore_missing',
                            default=False,
                            help='Ignore missing source file error and '
                                 'skip render for that file')

    def handle(self, *args, **options):
        replace = options.get('replace', False)
        ignore_missing = options.get('ignore_missing', False)
        routes = options.get('field_path', [])
        for route in routes:
            try:
                app_label, model_name, field_name = route.rsplit('.')
            except ValueError:
                raise CommandError("Error parsing field_path '{}'. Use format "
                                   "<app.model.field app.model.field>."
                                   .format(route))
            model_class = apps.get_model(app_label, model_name)
            field = model_class._meta.get_field(field_name)

            queryset = model_class._default_manager \
                .exclude(**{'%s__isnull' % field_name: True}) \
                .exclude(**{field_name: ''})
            obj = queryset.first()
            do_render = True
            if obj:
                f = getattr(obj, field_name)
                do_render = f.field.render_variations
            images = queryset.values_list(field_name, flat=True).iterator()
            count = queryset.count()

            self.render(field, images, count, replace, ignore_missing,
                        do_render)

    @staticmethod
    def render(field, images, count, replace, ignore_missing, do_render):
        kwargs_list = (
            dict(
                file_name=file_name,
                do_render=do_render,
                variations=field.variations,
                replace=replace,
                storage=field.storage.deconstruct()[0],
                field_class=field.attr_class,
                ignore_missing=ignore_missing,
            )
            for file_name in images
        )
        with progressbar.ProgressBar(max_value=count, widgets=(
            progressbar.RotatingMarker(),
            ' | CPUs: {}'.format(cpu_count()),
            ' | ', progressbar.AdaptiveETA(),
            ' | ', progressbar.Percentage(),
            ' ', progressbar.Bar(),
        )) as bar:
            with ProcessPoolExecutor() as executor:
                for _ in executor.map(render_field_variations, kwargs_list):
                    bar += 1


def render_field_variations(kwargs):
    kwargs['storage'] = get_storage_class(kwargs['storage'])()
    ignore_missing = kwargs.pop('ignore_missing')
    do_render = kwargs.pop('do_render')
    try:
        if callable(do_render):
            kwargs.pop('field_class')
            do_render = do_render(**kwargs)
        if do_render:
            render_variations(**kwargs)
    except FileNotFoundError as e:
        if not ignore_missing:
            raise CommandError(
                 'Source file was not found, terminating. '
                 'Use -i/--ignore-missing to skip this error.') from e
