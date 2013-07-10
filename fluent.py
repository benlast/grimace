"""
Fluent functional interface for grimace.

The target use case is something like:

    from grimace.fluent import RE    # (bad practice, you wouldn't normally do this)
    my_re = RE().start().literal('/blog/').capture_named('asset_id',zero_or_more(digit()))

"""
__author__ = 'BenL'

import types


class REElement(object):
    """Parent class for all elements that mark RE behaviour"""

    def marker(self):
        """Emit any marker string for this element"""
        return ""


class PostfixGeneratingREElement(REElement):
    """Parent class for all elements that generate postfix strings"""

    def postfix_marker(self):
        return ""


class Repeater(PostfixGeneratingREElement):
    """A Repeater modifies the repeat count of the FOLLOWING element.
    It's an edge case because the marker for it must be emitted after the
    following element, but fluency implies that the repeater comes
    first.  E.g. one_or_more().digit()"""

    # TODO - greedy markers

    def __init__(self, minimum=0, maximum=1):
        """maximum may be negative to mean any number of repeats"""
        self.minimum = minimum
        self.maximum = maximum

    def postfix_marker(self):
        """Return the appropriate postfix repeat marker"""
        if self.minimum == 0:
            if self.maximum < 0:
                return '.'
            elif self.maximum == 1:
                return '?'
        elif self.minimum == 1:
            if self.maximum < 0:
                return '+'
        return "{%d,%d}" % (self.minimum, self.maximum)


class StartCapture(REElement):
    """ A StartGroup puts FOLLOWING RE elements in a capture.
    The end of the capture is marked by the next EndCapture"""

    def __init__(self, capture_name=None):
        """If capture_name is None, this is a un-named capture"""
        self.capture_name = capture_name

    def marker(self):
        """Return the appropriate prefix marker for the capture"""
        #TODO - verify the syntax here
        if self.capture_name:
            return "(?P<%s>" % self.capture_name
        else:
            return "("


class EndCapture(REElement):
    """An EndGroup ends a capture"""

    def marker(self):
        return ')'


class Not(REElement):
    """ A Not object inverts the matching sense of the FOLLOWING character class"""
    pass


class FormatError(Exception):
    """The RE is badly formatted"""
    def __init__(self, message="The expression is incorrectly formatted"):
        self.message = message


class RE(object):
    """Class that represents a regexp string being assembled.
    To support the fluent syntax, start with an instance of this class
    and then call methods on it, each of which will yield a new instance
    that is extended.
    When done, a str() will return the regexp string.
    """

    # The list of elements that an RE holds
    elements = []

    def __init__(self, *args):
        """
        Create a new RE - the core of an RE is a list of strings or REElements, which
        grows with each addition (or has the tail element modified in some cases)
        until stringified at the end.
        If args are supplied: the elements list for this instance is built up by adding
        the elements lists from any args that are instances of this class, and any strings
        or unicode strings or REElements.
        """
        if args:
            self.elements = reduce(RE.reducer, args, [])

    @staticmethod
    def is_legal_element(e):
        """Return True if the e is an acceptable string or an RE element"""
        return (type(e) in types.StringTypes) or isinstance(e, REElement)

    @staticmethod
    def reducer(elements, arg):
        """Reducing function to be applied over supplied element lists
        to combine them.
        If arg is a string, return elements with the string appended.
        If arg is an REElement, return elements with it appended.
        If arg is an iterable, return elements with the elements of arg appended.
        If arg is an instance of this class, return elements with the elements of that
        instance appended.
        """
        if isinstance(arg, RE):
            return elements + arg.elements  # Concatenate lists
        elif RE.is_legal_element(arg):
            return elements + [arg]
        try:
            # Assume the arg is an iterable and add all legal items from it to elements
            # by recursing.
            return reduce(RE.reducer, arg, elements)
        except TypeError:
            # raised if arg is not iterable, in which case we silently ignore it
            pass

    def stringify(self):
        """Convert all elements to strings (or unicodes) and return a list of them.
         This also performs some validity checks on the RE."""

        # An empty list returns an empty string
        if not self.elements:
            return ""

        # We know the list is not empty, so check that the end element is not one that
        # requires at least one following element.
        trailing_element = self.elements[-1]
        if any(isinstance(trailing_element, k) for k in (StartCapture, Not)):
            raise FormatError("The expression cannot end with this element")

        # The list processing here is a little complex, because we allow for an REElement
        # that affects the element FOLLOWING it by emitting text that comes after that following
        # element.  The best example is zero_or_more().digit() which results in
        # [Repeater(0,-1), '\d'] and has to be stringified as "\d*" where the '*' comes from
        # the Repeater.
        # We can generalize this to:
        #   Wherever an element e is an REElement object, emit e's marker, then the result of stringifying
        #   the following element, then emit e's postfix_marker.
        # This is actually quite a nice little functional programming problem: how can you do this
        # with a processor that consumes one element at a time?  The answer is by reducing,
        # and inspecting the end of the accumulated list for postfix-generating
        # elements.

        def string_reducer(elements, e):
            # If e is a postfix-generating REElement, then just add it to the end of the elements list
            if isinstance(e, PostfixGeneratingREElement):
                return elements + [e]

            # Get the string or unicode version of the element
            s = e if type(e) in types.StringTypes else e.marker()

            # If s is empty, then we just return the elements list as it is.  This means that
            # any postfix-generator currently at the end of the list won't be consumed - we consider
            # that it should modify only the following non-empty string.
            if not s:
                return elements

            # If the tail of the list is a postfix-generator x, then return the elements list
            # without that generator, then s, then the postfix text from x
            if elements and isinstance(elements[-1], PostfixGeneratingREElement):
                pf = elements[-1]
                return elements[:-1] + s + pf.postfix_marker()

            # Just return elements with s appended
            return elements + [s]

        # Reduce to a list of strings or unicodes and return
        strings = reduce(string_reducer, self.elements, [])

        # Do one last pass in case there is a lingering postfix-generator in the list, which was left
        # because there was an empty string following it.
        return [x for x in strings if type(x) in types.StringTypes]

    def __unicode__(self):
        """Return the regexp as Unicode, decoding any strings from ascii if required."""
        return u"".join((x if isinstance(x, unicode) else x.decode('ascii') for x in self.stringify()))

    def __str__(self):
        """Return the regexp as a string, encoding any unicode elements to ascii if required, which means there
        may be an EncodingError raised."""
        return "".join((x if isinstance(x, str) else x.encode('ascii') for x in self.stringify()))

    def as_string(self):
        return self.__unicode__()

    def ends_with_not(self):
        """Return True if the current elements list ends with a Not"""
        return self.elements and isinstance(self.elements[-1], Not)

    # The remaining methods are fluent

    def start(self):
        """Add the start anchor ^ to the regexp"""
        return RE(self, '^')

    def end(self):
        """Add the end anchor '$' to the regexp"""
        return RE(self, '$')

    # Character classes
    backslash = "\\"
    metacharacters = r".^$*+?{}[]\|()"

    @staticmethod
    def escape(c):
        """Return the character c as-is, unless it is a metacharacter, in
         which case return it preceded by a backslash"""
        return RE.backslash+c if c in RE.metacharacters else c

    def literal(self, s):
        """Add the literal string s to the regexp, escaping any metacharacters in it"""
        escaped = ''.join(map(RE.escape, s))
        return RE(self, escaped)

    def digit(self):
        """Adds a digit '\d' specifier to the regexp, but invert to
        '\D' if the preceding element is a Not"""
        if self.ends_with_not():
            return RE(self.elements[:-1], r'\D')
        return RE(self, r'\d')

    def digits(self):
        """A synonym for digit"""
        return self.digit()

    def whitespace(self):
        """Adds a whitespace '\s' specifier to the regexp, but invert to
        '\S' if the preceding element is a Not"""
        if self.ends_with_not():
            return RE(self.elements[:-1], r'\S')
        return RE(self, r'\s')

    def alphanumeric(self):
        """Adds an alphanumeric '\w' specifier to the regexp - this matches
        any of a-z, A-Z or 0-9.  If the preceding element is a Not, invert
        the match to a '\W'"""
        if self.ends_with_not():
            return RE(self.elements[:-1], r'\W')
        return RE(self, r'\w')

    def any_of(self, s):
        """Match on any of the characters in the string s.  If the preceding element
        is a Not, invert the sense of the match."""
        charset = ''.join(map(RE.escape, s))
        if self.ends_with_not():
            return RE(self.elements[:-1], "[^%s]" % charset)
        return RE(self, "[%s]" % charset)

    # repeat filters
    def zero_or_more(self):
        """The FOLLOWING element matches when repeated zero or more times"""
        return RE(self, Repeater(minimum=0, maximum=-1))

    def zero_or_once(self):
        """The FOLLOWING element matches when repeated zero or once"""
        return RE(self, Repeater(minimum=0, maximum=1))

    def one_or_more(self):
        """The FOLLOWING element matches when repeated one or more times"""
        return RE(self, Repeater(minimum=1, maximum=-1))

    def exactly(self, n):
        """The FOLLOWING element matches when repeated n times"""
        return RE(self, Repeater(minimum=n, maximum=n))

    def between(self, n, m):
        """The FOLLOWING element matches when repeated at least n times and at most m times"""
        return RE(self, Repeater(minimum=n, maximum=m))

    # groupings of RE objects
    def any_re(self, *args):
        """Match on any of the args, which can be RE objects or strings"""
        return RE(self, '|'.join(unicode(x) for x in args))

# Unit tests go below here

import unittest


class Tests(unittest.TestCase):

    def runTest(self):
        self.assertEqual(RE().start().end().as_string(), "^$")
        self.assertEqual(RE().start().literal("hello").end().as_string(), "^hello$")
