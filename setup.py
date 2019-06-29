#!/usr/bin/env python
import distutils
import glob
import os
import subprocess  # nosec
from distutils.cmd import Command
from distutils.command.build import build as _build

from setuptools import setup
from setuptools.command.install_lib import install_lib as _install_lib

BASE_DIR = os.path.dirname((os.path.abspath(__file__)))


class compile_translations(Command):
    description = 'Compile i18n translations using gettext.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pattern = 'stdimage/locale/*/LC_MESSAGES/django.po'
        for file in glob.glob(pattern):
            cmd = ['msgfmt', '-c']
            name, ext = os.path.splitext(file)

            cmd += ['-o', '%s.mo' % name]
            cmd += ['%s.po' % name]
            self.announce(
                'running command: %s' % ' '.join(cmd),
                level=distutils.log.INFO)
            subprocess.check_call(cmd, cwd=BASE_DIR)  # nosec


class build(_build):
    sub_commands = [('compile_translations', None)] + _build.sub_commands


class install_lib(_install_lib):
    def run(self):
        self.run_command('compile_translations')
        _install_lib.run(self)


setup(
    use_scm_version=True,
    cmdclass={
        'build': build,
        'install_lib': install_lib,
        'compile_translations': compile_translations,
    },
)
