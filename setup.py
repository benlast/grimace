#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
import codecs
from os import path
from setuptools import setup, find_packages
from _version import __version__


def content_of(paths, encoding='utf-8', sep='\n'):
    if isinstance(paths, str):
        paths = [paths]
    content = []
    for path in paths:
        with codecs.open(path, encoding=encoding) as stream:
            content.append(stream.read())
    return sep.join(content)


here = path.abspath(path.dirname(__file__))

setup(name='grimace',
      version=__version__,
      description='A fluent regular expression generator',
      long_description=content_of(path.join(here, 'README.rst')),
      author='Ben Last',
      author_email='ben@benlast.com',
      url='https://github.com/benlast/grimace',
      license='MIT, Academic Free License version 2.1',
      classifiers=[  # http://pypi.python.org/pypi?:action=list_classifiers
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'License :: OSI Approved :: Academic Free License (AFL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development :: Code Generators',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords=['re', 'regex', 'regexp', 'regular expression', 'fluent'],
      install_requires=['nine'],
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='grimace.tests',
)
