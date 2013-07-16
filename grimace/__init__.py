"""
grimace - a fluent regular expression package for Python.
(c) 2013 ben last <ben@benlast.com>
See the LICENSE file for licence terms (MIT, AFL)
"""

__author__ = 'ben last <ben@benlast.com>'

# TODO - lookahead assertions - suggest .lookahead_match, .lookahead_end, and allow inversion via not_a
# TODO - MULTILINE mode?
# TODO - combining REs

from grimace.extender import Extender
from grimace.elements import RE, FormatError
