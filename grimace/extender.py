# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class Extender(object):
    """
    An Extender is a descriptor intended for use with RE objects,
    whose __get__ method returns a new RE based on the RE on which it
    was invoked, but with the elements extended with a given
    element, set when the Extender is initialized.  It exists so
    that methods like start() and end() can be invoked as attributes or
    methods.

    For extenders that need to add an alternate element if the existing
    RE ends with a Not, an alternate may be passed to init; this is the
    element added if a Not is present.
    """
    def __init__(self, element=None, alternate=None):
        self.element = element
        self.alternate = alternate if alternate is not None else self.element

    def __get__(self, instance, klass):
        """
        Args:
            instance: RE instance
            klass: RE class

        Returns:
            RE
        """
        # If the instance has an ends_with_not attribute, call it,
        # otherwise assume False. This avoids us having too awkward a
        # circular reference between the RE class and this class.
        ends_with_not = getattr(instance, "ends_with_not", lambda x: False)()
        element = self.alternate if ends_with_not else self.element
        if element is not None:
            return klass(instance, element)

        else:
            return klass(instance)
