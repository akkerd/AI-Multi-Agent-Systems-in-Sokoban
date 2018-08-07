#!/usr/bin/env python3
from setuptools import setup, find_packages

from setuptools.command.install import install
setup(name='searchclient',
      use_scm_version=True,
      #cmdclass={'install': QleInstall, 'sdist' : QleSdist}, #Extend install, could make another cmd instead
      description='Searchclient For 02285 AI and MAS',
      author='Mathias R. Bjare',
      author_email='mathias@bjare.dk',
      install_requires = ['psutil','nose','dataclasses', 'scipy', 'numpy'],
      #dependency_links = ['http://effbot.org/downloads/'],
      package_dir = {'': 'src/searchclient'},
      packages= find_packages('src/searchclient'),
      setup_requires=['pytest-runner','setuptools_scm','pytest'],
      tests_require=['pytest'],
      test_suite='test',
      )

