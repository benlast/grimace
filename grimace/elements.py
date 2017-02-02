# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
import re
from functools import reduce  # which is no longer a builtin in Python 3.
from nine import basestring, str, nine
from .extender import Extender


class REElement(object):
    """
    Parent class for all elements that mark RE behaviour
    """

    def marker(self):
        """
        Emit any marker string for this element
        Returns:
            str: the marker string
        """
        return ''


class PostfixGeneratingREElement(REElement):
    """
    Parent class for all elements that generate postfix strings
    """

    def postfix_marker(self):
        """
        Emit any marker string for this element
        Returns:
            str: the marker string
        """
        return ''


class Repeater(PostfixGeneratingREElement):
    """
    A Repeater modifies the repeat count of the FOLLOWING element.
    It's an edge case because the marker for it must be emitted after the
    following element, but fluency implies that the repeater comes
    first.  E.g. one_or_more().digit()
    """

    def __init__(self, minimum=0, maximum=1, greedy=True):
        """
        Args:
            minimum (int): minimum number of repeats, default 0
            maximum (int): maximum number of repeats, may be -1 for
                any number of repeats.
            greedy (bool): True for greedy matching, False for non-greedy
        """
        self.minimum = minimum
        self.maximum = maximum
        self.greedy = greedy

    def postfix_marker(self):
        """
        Return the appropriate postfix repeat marker
        Returns:
            str: the postfix marker string
        """
        if self.minimum == 0:
            if self.maximum < 0:
                return '*' if self.greedy else '*?'
            elif self.maximum == 1:
                return '?' if self.greedy else '??'
        elif self.minimum == 1:
            if self.maximum < 0:
                return '+' if self.greedy else '+?'
        return '{%d,%d}%s' % (
            self.minimum,
            self.maximum,
            '' if self.greedy else '?'
        )


class StartGroup(REElement):
    """
    A StartGroup puts FOLLOWING RE elements in a group.
    The end of the group is marked by the next EndCapture
    """

    def __init__(self, name=None):
        """
        Args:
            name (str): the group name. If name is None (default),
                then this is a un-named group
        """
        self.group_name = name

    def marker(self):
        """
        Return the appropriate prefix marker for the group
        Returns:
            str: the prefix marker string
        """
        if self.group_name:
            return '(?P<%s>' % self.group_name
        else:
            return '('


class EndGroup(REElement):
    """
    An EndGroup ends a group
    """

    def marker(self):
        return ')'


class Not(REElement):
    """
    A Not object inverts the matching sense of the FOLLOWING character
    class, or the greediness of the FOLLOWING repeat marker
    """
    pass


class FormatError(Exception):
    """
    The RE is badly formatted
    """

    def __init__(self, message="The expression is incorrectly formatted"):
        self.message = message


@nine
class RE(object):
    """
    Class that represents a regexp string being assembled.
    To support the fluent syntax, start with an instance of this class
    and then call methods on it, each of which will yield a new instance
    that is extended.
    When done, a str() will return the regexp string.

    Attributes:
        elements (list(REElement): the set of elements of this RE
    """

    # The list of elements that an RE holds
    elements = []

    def __init__(self, *args):
        """
        Create a new RE - the core of an RE is a list of strings or
        REElements, which grows with each addition (or has the tail
        element modified in some cases) until stringified at the end.
        If args are supplied: the elements list for this instance is built
        up by adding the elements lists from any args that are instances
        of this class, and any strings or unicode strings or REElements.
        """
        if args:
            self.elements = reduce(RE.__reducer, args, [])

        # Add no-op and other attributes that may be invoked as
        # attributes or methods
        self.then = self
        self.followed_by = self
        self.of = self.of_a = self.of_an = self

    def __call__(self, *args, **kwargs):
        """
        Calling an RE object returns a reference to that same object.  This
        is done to support no-ops like then() and followed_by() such that
        they can be invoked as attributes or methods.

        If args are passed, then call returns a new RE that has the given
        args appended.  This allows 'of' to work as a conjunction or a way
        to add previously generated REs

        Returns:
            RE
        """
        if args:
            return RE(self, *args)

        return self

    @staticmethod
    def __is_legal_element(e):
        """
        Returns:
            bool: True if the e is an acceptable string or an RE element,
                False otherwise
        """
        return isinstance(e, (basestring, REElement))

    @staticmethod
    def __reducer(elements, arg):
        """
        Reducing function to be applied over supplied element lists
        to combine them.

        If arg is a string, return elements with the string appended.
        If arg is an REElement, return elements with it appended.
        If arg is an iterable, return elements with the elements of arg
        appended.
        If arg is an instance of this class, return elements with the
        elements of that instance appended.

        Returns:
            list: list of RE, REElement or strings
        """
        if isinstance(arg, RE):
            return elements + arg.elements  # Concatenate lists

        elif RE.__is_legal_element(arg):
            return elements + [arg]

        try:
            # Assume the arg is an iterable and add all legal items from
            # it to elements by recursing.
            return reduce(RE.__reducer, arg, elements)

        except TypeError:
            # raised if arg is not iterable, in which case we silently
            # ignore it
            pass

    def __stringify(self):
        """
        Convert all elements to strings (or unicodes) and return a list
        of them.
        Also performs some validity checks on the RE.
        Returns:
            list of str
        """

        # An empty list returns an empty string
        if not self.elements:
            return ""

        # We know the list is not empty, so check that the end element
        # is not one that requires at least one following element.
        trailing_element = self.elements[-1]
        if any(isinstance(trailing_element, k) for k in (StartGroup, Not)):
            raise FormatError("The expression cannot end with this element")

        # Verify that every StartGroup is matched by an EndGroup.  This
        # isn't as simple as checking that the counts match - we must also
        # spot an EndGroup coming before any StartGroup and vice versa.
        # It's worth doing this because the whole point of grimace is to
        # make it easier to write regexp's and mismatched groups are
        # an error.

        # Start by finding the indexes of all start and end groups
        start_group_indices = [
            i
            for i, x in enumerate(self.elements)
            if isinstance(x, StartGroup)
        ]
        end_group_indices = [
            i
            for i, x in enumerate(self.elements)
            if isinstance(x, EndGroup)
        ]

        # Check that there are the same number of starts and ends
        if len(start_group_indices) != len(end_group_indices):
            raise FormatError(
                'The expression contains different numbers of start_group '
                'and end_group elements'
            )

        # If there's at least one group, then we will check for
        # end-before-start or start-after-end
        if len(start_group_indices) > 0:
            if end_group_indices[0] < start_group_indices[0]:
                raise FormatError(
                    'An end_group comes before the first start_group'
                )
            elif start_group_indices[-1] > end_group_indices[-1]:
                raise FormatError(
                    'A start_group comes after the last end_group'
                )

        # The list processing here is a little complex, because we allow
        # for an REElement that affects the element FOLLOWING it by
        # emitting text that comes after that following element.  The best
        # example is zero_or_more().digit() which results in
        # [Repeater(0,-1), '\d'] and has to be stringified as "\d*"
        # where the '*' comes from the Repeater.

        # We can generalize this to:
        #   Wherever an element e is an REElement object, emit e's marker,
        #   then the result of stringifying the following element, then
        #   emit e's postfix_marker.
        # This is actually quite a nice little functional programming
        # problem: how can you do this with a processor that consumes one
        # element at a time?  The answer is by reducing, and inspecting
        # the end of the accumulated list for postfix-generating
        # elements.

        def string_reducer(elements, e):
            # If e is a postfix-generating REElement, then just add it to
            # the end of the elements list
            if isinstance(e, PostfixGeneratingREElement):
                return elements + [e]

            # Get the string or unicode version of the element
            s = e if isinstance(e, basestring) else e.marker()

            # If s is empty, then we just return the elements list as it
            # is.  This means that any postfix-generator currently at the
            # end of the list won't be consumed - we consider
            # that it should modify only the following non-empty string.
            if not s:
                return elements

            # If the tail of the list is a postfix-generator x, then return
            # the elements list without that generator, then s, then the
            # postfix text from x
            if elements and isinstance(elements[-1], PostfixGeneratingREElement):
                return elements[:-1] + [s, elements[-1].postfix_marker()]

            # Just return elements with s appended
            return elements + [s]

        # Reduce to a list of strings or unicodes and return
        strings = reduce(string_reducer, self.elements, [])

        # Do one last pass in case there is a lingering postfix-generator
        # in the list, which was left because there was an empty string
        # following it.
        return [x for x in strings if isinstance(x, basestring)]

    def __str__(self):
        """
        Return the regexp as a unicode string, decoding any bytestrings.
        Returns:
            str
        """
        return ''.join(
            x if isinstance(x, str) else x.decode('ascii')
            for x in self.__stringify()
        )

    def ends_with_not(self):
        """
        Returns:
             bool: True if the current elements list ends with a Not
        """
        # This is technically a private method, but it's not mangle-named
        # so that the Extender class may use it.
        return self.elements and isinstance(self.elements[-1], Not)

    # Result methods

    def as_string(self):
        """
        Returns:
            str: the string generated by the expression
        """
        return str(self)

    # Constants that match some of those in the re module, to save
    # the caller having to import both
    IGNORECASE = re.IGNORECASE
    LOCALE = re.LOCALE
    UNICODE = re.UNICODE
    DEBUG = re.DEBUG

    def as_re(self, flags=0):
        """
        Return a compiled regular expression object.  The flags parameter
        is passed to re.compile.  However, the only real use for it is to
        pass re.IGNORECASE, re.LOCALE or re.UNICODE.

        Returns:
            re.RegexObject
        """
        return re.compile(str(self), flags)

    # The remaining methods are fluent

    start = Extender('^')
    end = Extender('$')

    # Character classes
    backslash = "\\"
    metacharacters = r".^$*+?{}[]\|()-"

    @staticmethod
    def escape(c):
        """
        Returns:
            str: the character c as-is, unless it is a metacharacter, in
                which case return it preceded by a backslash
        """
        return RE.backslash + c if c in RE.metacharacters else c

    # Basic elements, character classes

    def literal(self, s):
        """
        Add the literal string s to the regexp, escaping any
        metacharacters.
        Returns:
            RE
        """
        return RE(self, ''.join(map(RE.escape, s)))

    def regex(self, s):
        """
        Add the given string to the regex without any escaping, so that
        legal regex character groupings may be used.
        Returns:
            RE
        """
        return RE(self, s)

    digits = digit = Extender(r'\d', r'\D')
    """
    Adds a digit '\d' specifier to the regexp, but invert to '\D' if
    the preceding element is a Not.
    Returns:
        RE
    """

    whitespace = Extender(r'\s', r'\S')
    """
    Adds a whitespace '\s' specifier to the regexp, but invert to
    '\S' if the preceding element is a Not
    Returns:
        RE
    """

    alphanumerics = alphanumeric = Extender(r'\w', r'\W')
    """
    Adds an alphanumeric '\w' specifier to the regexp - this matches
    any of a-z, A-Z or 0-9.  If the preceding element is a Not, invert
    the match to a '\W'
    Returns:
        RE
    """

    alpha = alphas = a_to_z = Extender(r'[a-zA-Z]', r'[^a-zA-Z]')
    """
    Adds an alpha specifier to the regexp - this matches
    any of a-z, A-Z.  If the preceding element is a Not, invert
    the match.
    Returns:
        RE
    """

    identifier = Extender(r'[a-zA-Z_][\w_]*')
    """
    Match an identifier - this is an alpha or underscore
    followed by zero or more alphanumerics or underscores.
    Returns:
        RE
    """

    word_boundary = Extender(r'\b', r'\B')
    """
    Adds an word-boundary '\b' specifier to the regexp: may be inverted by a
    preceding Not.
    Returns:
        RE
    """

    def any_of(self, s):
        """
        Match on any of the characters in the string s, treated as
        LITERALS, and escaped.  If you want to put an actual RE expression
        such as [a-z] in, use regex().
        If the preceding element is a Not, invert the sense of the match.
        Returns:
            RE
        """
        charset = ''.join(map(RE.escape, s))
        if self.ends_with_not():
            return RE(self.elements[:-1], "[^%s]" % charset)

        return RE(self, "[%s]" % charset)

    # repeat filters
    any_number_of = zero_or_more = Extender(Repeater(minimum=0, maximum=-1),
                                            Repeater(minimum=0, maximum=-1,
                                                     greedy=False))
    """
    The FOLLOWING element matches when repeated zero or more times
    Returns:
        RE
    """

    an_optional = optional = zero_or_one = zero_or_once = Extender(Repeater(minimum=0, maximum=1),
                                                                   Repeater(minimum=0, maximum=1,
                                                                            greedy=False))
    """
    The FOLLOWING element matches when repeated zero or once
    Returns:
        RE
    """

    at_least_one = one_or_more = Extender(Repeater(minimum=1, maximum=-1),
                                          Repeater(minimum=1, maximum=-1, greedy=False))
    """
    The FOLLOWING element matches when repeated one or more times.
    Returns:
        RE
    """

    def exactly(self, n):
        """
        The FOLLOWING element matches when repeated n times - greediness
        is not relevant for this repeat match.
        Returns:
            RE
        """
        return RE(self, Repeater(minimum=n, maximum=n))

    a = an = one = Extender(Repeater(minimum=1, maximum=1))
    """
    Synonym for exactly(1)
    Returns:
        RE
    """

    def up_to(self, n):
        """
        The FOLLOWING element matches when repeated up to n times.
        greediness is not relevant for this repeat match.
        Returns:
            RE
        """
        return RE(self, Repeater(minimum=0, maximum=n))

    def between(self, n, m):
        """
        The FOLLOWING element matches when repeated at least n times and at most m times.
        greediness is not relevant for this repeat match.
        Returns:
            RE
        """
        return RE(self, Repeater(minimum=min(n, m), maximum=max(n, m)))

    # Convenience methods

    dot = Extender(r'\.')
    """
    Add a literal '\.'
    Returns:
        RE
    """

    underscore = Extender('_')
    """
    Add a literal underscore
    Returns:
        RE
    """

    dash = Extender(r'\-')
    """
    Add a literal dash
    Returns:
        RE
    """

    anything = Extender(r'.*', r'.*?')
    """
    Add a .* that will match anything (greedy or non-greedy)
    Returns:
        RE
    """

    any_character = Extender(r'.')
    """
    Add a . that will match any character
    Returns:
        RE
    """

    newline = Extender(r'\\n')
    """
    Add a \n that will match a newline
    Returns:
        RE
    """

    tab = Extender(r'\\t')
    """
    Add a \r that will match a tab
    Returns:
        RE
    """

    # Logical

    not_an = not_a = non_greedy = Extender(Not())
    """
    Add a Not element, that inverts the next applicable
    element.  Since not is a reserved word in Python, we
    call this method not_a.
    Returns:
        RE
    """

    # Capturing
    start_group = group = Extender(StartGroup())
    """
    Start a named or un-named group
    Returns:
        RE
    """

    def named_group(self, name=None):
        """
        Start a named or un-named group
        Returns:
            RE
        """
        return RE(self, StartGroup(name=name))

    start_named_group = named_group
    """
    synonym for group
    Returns:
        RE
    """

    end_group = Extender(EndGroup())
    """
    End a capture group
    Returns:
        RE
    """

    # groupings of RE objects
    def any_re(self, *args):
        """
        Match on any of the args, which can be RE objects or strings
        Returns:
            RE
        """
        return RE(
            self,
            '|'.join(
                x.as_string()
                if isinstance(x, RE) else str(x)
                for x in args
            )
        )
