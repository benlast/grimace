# -*- coding: utf-8 -*-

"""
grimace - a fluent regular expression package for Python.
(c) 2017 ben last <ben@benlast.com>
See the LICENSE file for licence terms (MIT, AFL)
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# TODO - lookahead assertions - suggest .lookahead_match, .lookahead_end, and allow inversion via not_a
# TODO - MULTILINE mode?
# TODO - combining REs

from .extender import Extender
from .elements import RE, FormatError
