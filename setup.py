__author__ = 'benlast <ben@benlast.com>'

from distutils import setup
from _version import __version__

setup(name='grimace',
      version=__version__,
      description='A fluent regular expression generator',
      author='Ben Last',
      author_email='ben@benlast.com',
      url='',
      packages=['grimace'],
)
