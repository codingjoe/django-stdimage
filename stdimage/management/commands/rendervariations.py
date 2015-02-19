# -*- coding: utf-8 -*-
from __future__ import (absolute_import, unicode_literals)
import resource

from django.core.management import BaseCommand
from django.db.models import get_model
import progressbar


class MemoryUsageWidget(progressbar.widgets.Widget):
    def update(self, pbar):
        return 'RAM: {0:10.1f} MB'.format(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        )


class CurrentInstanceWidget(progressbar.WidgetHFill):
    def update(self, pbar, width):
        return 'Object: {0}@pk={1}'.format(pbar.instance, pbar.instance.pk)


class Command(BaseCommand):
    help = 'Renders all variations of a StdImageField.'
    args = '<app.model.field app.model.field>'

    def add_arguments(self, parser):
        parser.add_argument('--replace',
                            action='store_true',
                            dest='replace',
                            default=False,
                            help='Replace existing files.')

    def handle(self, *args, **options):
        replace = options.get('replace')
        for route in args:
            pk = None
            app_name, model_name, field_name = route.rsplit('.')
            if '@' in field_name:
                field_name, pk = field_name.split('@', 1)
            model_class = get_model(app_name, model_name)
            queryset = model_class.objects \
                .exclude(**{'%s__isnull' % field_name: True}) \
                .exclude(**{field_name: ''}) \
                .order_by('pk')
            if pk:
                queryset = queryset.filter(pk__gte=pk)
            total = queryset.count()
            prog = progressbar.ProgressBar(maxval=total, widgets=(
                progressbar.RotatingMarker(),
                ' | ', MemoryUsageWidget(),
                ' | ', progressbar.ETA(),
                ' | ', progressbar.Percentage(),
                ' ', progressbar.Bar(),
                ' ', CurrentInstanceWidget(),
            ))
            i = 0
            for instance in queryset:
                field_file = getattr(instance, field_name)
                field = field_file.field
                prog.instance = instance
                prog.update(i)
                for name, variation in field.variations.items():
                    field_file.render_and_save_variation(
                        field_file,
                        variation,
                        replace
                    )
                field_file.close()
                i += 1
            prog.finish()
