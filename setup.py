#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name='django-stdimage',
    version='2.3.3',
    description='Django Standarized Image Field',
    author='codingjoe',
    url='https://github.com/codingjoe/django-stdimage',
    download_url='https://github.com/codingjoe/django-stdimage',
    author_email='info@johanneshoppe.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
    ],
    packages=find_packages(exclude=[
        "*.tests", "*.tests.*", "tests.*", "tests", ".egg-info"
    ]),
    include_package_data=True,
    install_requires=[
        'pillow>=2.5',
        'progressbar2>=3.0.0',
    ],
)
