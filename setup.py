__author__ = 'benlast <ben@benlast.com>'

from distutils.core import setup
from _version import __version__

setup(name='grimace',
      version=__version__,
      description='A fluent regular expression generator',
      author='Ben Last',
      author_email='ben@benlast.com',
      url='https://github.com/benlast/grimace/wiki',
      license='MIT, Academic Free License version 2.1',
      packages=['grimace'],
)
