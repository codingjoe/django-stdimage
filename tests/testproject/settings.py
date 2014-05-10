# -*- coding: utf-8 -*-
import os

SECRET_KEY = '5@ue^&26720sPOIAdg01k%!v2ulhf_sjc6-$d1'

DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'testproject.db'

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en'

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

MEDIA_URL = '/media/'

ADMIN_MEDIA_PREFIX = '/admin_media/'

SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'testproject.urls'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'stdimage',
    'testproject',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)
