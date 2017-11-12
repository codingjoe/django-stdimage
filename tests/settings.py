# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import os
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'stdimage',
    'tests'
)

DEFAULT_FILE_STORAGE = 'tests.storage.MyFileSystemStorage'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    }
]

MIDDLEWARE = MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

MEDIA_ROOT = tempfile.mkdtemp()

SITE_ID = 1
ROOT_URLCONF = 'tests.urls'

SECRET_KEY = 'foobar'

USE_L10N = True
