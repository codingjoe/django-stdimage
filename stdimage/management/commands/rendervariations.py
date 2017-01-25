# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import sys
import traceback
from multiprocessing import Pool, cpu_count

import progressbar
from django.apps import apps
from django.core.files.storage import get_storage_class
from django.core.management import BaseCommand, CommandError

from stdimage.utils import render_variations

try:
    import resource
except ImportError:
    resource = None


BAR = None


class MemoryUsageWidget(progressbar.widgets.WidgetBase):
    def __call__(self, progress, data):
        if not resource:
            return 'RAM: N/A'
        return 'RAM: {0:10.1f} MB'.format(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        )


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

    def handle(self, *args, **options):
        replace = options.get('replace')
        if len(options['field_path']):
            routes = options['field_path']
        else:
            routes = [options['field_path']]
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

            self.render(field, images, count, replace, do_render)

    @staticmethod
    def render(field, images, count, replace, do_render):
        pool = Pool(
            initializer=init_progressbar,
            initargs=[count]
        )
        args = [
            dict(
                file_name=file_name,
                do_render=do_render,
                variations=field.variations,
                replace=replace,
                storage=field.storage.deconstruct()[0],
            )
            for file_name in images
        ]
        pool.map(render_field_variations, args)
        pool.apply(finish_progressbar)
        pool.close()
        pool.join()


def init_progressbar(count):
    global BAR
    BAR = progressbar.ProgressBar(maxval=count, widgets=(
        progressbar.RotatingMarker(),
        ' | ', MemoryUsageWidget(),
        ' | CPUs: {}'.format(cpu_count()),
        ' | ', progressbar.AdaptiveETA(),
        ' | ', progressbar.Percentage(),
        ' ', progressbar.Bar(),
    ))


def finish_progressbar():
    BAR.finish()


def render_field_variations(kwargs):
    try:
        kwargs['storage'] = get_storage_class(kwargs['storage'])()
        do_render = kwargs.pop('do_render')
        if callable(do_render):
            do_render = do_render(**kwargs)
        if do_render:
            render_variations(**kwargs)

        global BAR
        BAR += 1
    except:
        raise Exception("".join(traceback.format_exception(*sys.exc_info())))
