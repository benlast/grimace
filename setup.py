__author__ = 'benlast <ben@benlast.com>'

from distutils.core import setup
from _version import __version__
import sys


classifiers = """\
Development Status :: 4 - Beta
Intended Audience :: Developers
License :: OSI Approved :: MIT License
License :: OSI Approved :: Academic Free License (AFL)
Programming Language :: Python
Topic :: Software Development :: Code Generators
Topic :: Software Development :: Libraries :: Python Modules
Operating System :: Microsoft :: Windows
Operating System :: Unix
"""

kwargs = {
    'name': 'grimace',
    'version': __version__,
    'description': 'A fluent regular expression generator',
    'author': 'Ben Last',
    'author_email': 'ben@benlast.com',
    'url': 'https://github.com/benlast/grimace/wiki',
    'license': 'MIT, Academic Free License version 2.1',
    'packages': ['grimace'],
}

if sys.version >= (2, 3):
    kwargs['classifiers'] = classifiers.split('\n')

setup(**kwargs)
