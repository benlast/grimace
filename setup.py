#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
import codecs
import os
from setuptools import setup, find_packages
import sys
sys.path.append('.')


def content_of(paths, encoding='utf-8', sep='\n'):
    if isinstance(paths, str):
        paths = [paths]
    content = []
    for path in paths:
        with codecs.open(path, encoding=encoding) as stream:
            content.append(stream.read())
    return sep.join(content)


here = os.path.abspath(os.path.dirname(__file__))

VERSION = '0.1.2'

if '--grimace-version' in sys.argv:
    sys.stdout.write(VERSION)
    sys.exit(0)

setup(
    name='grimace',
    version=VERSION,
    description='A fluent regular expression generator',
    long_description=content_of(os.path.join(here, 'README.rst')),
    author='Ben Last',
    author_email='ben@benlast.com',
    url='https://github.com/benlast/grimace',
    license='MIT, Academic Free License version 2.1',
    classifiers=[  # http://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 5 - Production/Stable',
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
