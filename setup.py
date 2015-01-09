#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, Command, find_packages


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess

        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


setup(
    name='django-stdimage',
    version='1.2.0.1',
    description='Django Standarized Image Field',
    author='codingjoe',
    url='https://github.com/codingjoe/django-stdimage',
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
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", ".egg-info"]),
    include_package_data=True,
    requires=[
        'Pillow (>=2.5)',
        'progressbar (==2.2)',
    ],
    install_requires=[
        'pillow>=2.5',
        'progressbar==2.2',
    ],
    cmdclass={'test': PyTest},
)
