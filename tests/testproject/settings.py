# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'testproject.db'

# Django 1.4+ style of config
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'testproject.db'),
    }
}

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en'

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')

MEDIA_URL = '/media/'

ADMIN_MEDIA_PREFIX = '/admin_media/'

SECRET_KEY = 'x'

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
