"""
grimace - a fluent regular expression package for Python
"""

__author__ = 'ben last <ben@benlast.com>'
from _version import __version__, __version_info__

# TODO - greedy matching control
# TODO - MULTILINE mode?
# TODO - combining REs
# TODO - canned literals and other non-parameterized methods invoked as properties not methods?

import types
import re


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
                return '*'
            elif self.maximum == 1:
                return '?'
        elif self.minimum == 1:
            if self.maximum < 0:
                return '+'
        return "{%d,%d}" % (self.minimum, self.maximum)


class StartGroup(REElement):
    """ A StartGroup puts FOLLOWING RE elements in a group.
    The end of the group is marked by the next EndCapture"""

    def __init__(self, name=None):
        """If group_name is None, this is a un-named group"""
        self.group_name = name

    def marker(self):
        """Return the appropriate prefix marker for the group"""
        if self.group_name:
            return "(?P<%s>" % self.group_name
        else:
            return "("


class EndGroup(REElement):
    """An EndGroup ends a group"""

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
            self.elements = reduce(RE.__reducer, args, [])

    @staticmethod
    def __is_legal_element(e):
        """Return True if the e is an acceptable string or an RE element"""
        return (type(e) in types.StringTypes) or isinstance(e, REElement)

    @staticmethod
    def __reducer(elements, arg):
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
        elif RE.__is_legal_element(arg):
            return elements + [arg]
        try:
            # Assume the arg is an iterable and add all legal items from it to elements
            # by recursing.
            return reduce(RE.__reducer, arg, elements)
        except TypeError:
            # raised if arg is not iterable, in which case we silently ignore it
            pass

    def __stringify(self):
        """Convert all elements to strings (or unicodes) and return a list of them.
         This also performs some validity checks on the RE."""

        # An empty list returns an empty string
        if not self.elements:
            return ""

        # We know the list is not empty, so check that the end element is not one that
        # requires at least one following element.
        trailing_element = self.elements[-1]
        if any(isinstance(trailing_element, k) for k in (StartGroup, Not)):
            raise FormatError("The expression cannot end with this element")

        # Verify that every StartGroup is matched by an EndGroup.  This isn't as simple as
        # checking that the counts match - we must also spot an EndGroup coming before
        # any StartGroup and vice versa.  It's worth doing this because the whole point of
        # grimace is to make it easier to write regexp's and mismatched groups are an error.

        # Start by finding the indexes of all start and end groups
        start_group_indices = [i for i, x in enumerate(self.elements) if isinstance(x, StartGroup)]
        end_group_indices = [i for i, x in enumerate(self.elements) if isinstance(x, EndGroup)]

        # Check that there are the same number of starts and ends
        if len(start_group_indices) != len(end_group_indices):
            raise FormatError("The expression contains different numbers of start_group and end_group elements")

        # If there's at least one group, then we will check for end-before-start or start-after-end
        if len(start_group_indices) > 0:
            if end_group_indices[0] < start_group_indices[0]:
                raise FormatError("An end_group comes before the first start_group")
            elif start_group_indices[-1] > end_group_indices[-1]:
                raise FormatError("A start_group comes after the last end_group")

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
                return elements[:-1] + [s, elements[-1].postfix_marker()]

            # Just return elements with s appended
            return elements + [s]

        # Reduce to a list of strings or unicodes and return
        strings = reduce(string_reducer, self.elements, [])

        # Do one last pass in case there is a lingering postfix-generator in the list, which was left
        # because there was an empty string following it.
        return [x for x in strings if type(x) in types.StringTypes]

    def __unicode__(self):
        """Return the regexp as Unicode, decoding any strings from ascii if required."""
        return u"".join((x if isinstance(x, unicode) else x.decode('ascii') for x in self.__stringify()))

    def __str__(self):
        """Return the regexp as a string, encoding any unicode elements to ascii if required, which means there
        may be an EncodingError raised."""
        return "".join((x if isinstance(x, str) else x.encode('ascii') for x in self.__stringify()))

    def __ends_with_not(self):
        """Return True if the current elements list ends with a Not"""
        return self.elements and isinstance(self.elements[-1], Not)

    # Result methods

    def as_string(self):
        """Return the string generated by the expression"""
        return self.__unicode__()

    # Constants that match some of those in the re module, to save
    # the caller having to import both
    IGNORECASE = re.IGNORECASE
    LOCALE = re.LOCALE
    UNICODE = re.UNICODE
    DEBUG = re.DEBUG

    def as_re(self, flags=0):
        """Return a compiled regular expression object.  The flags parameter
        is passed to re.compile.  However, the only real use for it is to
        pass re.IGNORECASE, re.LOCALE or re.UNICODE."""
        return re.compile(self.__unicode__(), flags)

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
        return RE.backslash + c if c in RE.metacharacters else c

    # Basic elements, character classes

    def literal(self, s):
        """Add the literal string s to the regexp, escaping any metacharacters in it"""
        escaped = ''.join(map(RE.escape, s))
        return RE(self, escaped)

    def digit(self):
        """Adds a digit '\d' specifier to the regexp, but invert to
        '\D' if the preceding element is a Not"""
        if self.__ends_with_not():
            return RE(self.elements[:-1], r'\D')
        return RE(self, r'\d')

    def digits(self):
        """A synonym for digit"""
        return self.digit()

    def whitespace(self):
        """Adds a whitespace '\s' specifier to the regexp, but invert to
        '\S' if the preceding element is a Not"""
        if self.__ends_with_not():
            return RE(self.elements[:-1], r'\S')
        return RE(self, r'\s')

    def alphanumeric(self):
        """Adds an alphanumeric '\w' specifier to the regexp - this matches
        any of a-z, A-Z or 0-9.  If the preceding element is a Not, invert
        the match to a '\W'"""
        if self.__ends_with_not():
            return RE(self.elements[:-1], r'\W')
        return RE(self, r'\w')

    def alphanumerics(self):
        """Synonym for alphanumeric()"""
        return self.alphanumeric()

    def a_to_z(self):
        """Adds an alpha specifier to the regexp - this matches
        any of a-z, A-Z.  If the preceding element is a Not, invert
        the match"""
        if self.__ends_with_not():
            return RE(self.elements[:-1], r'[^a-zA-Z]')
        return RE(self.elements[:-1], r'[a-zA-Z]')

    def alpha(self):
        """Synonym for a_to_z()"""
        return self.a_to_z()

    def identifier(self):
        """Match an identifier - this is an alpha or underscore
        followed by zero or more alphanumerics or underscores"""
        return RE(self.elements[:-1], r'[a-zA-Z_][\w_]*')

    def alphanumerics(self):
        """Synonym for alphanumeric()"""
        return self.alphanumeric()

    def word_boundary(self):
        """Adds an word-boundary '\b' specifier to the regexp: may be inverted by a
        preceding Not"""
        if self.__ends_with_not():
            return RE(self.elements[:-1], r'\B')
        return RE(self, r'\b')

    def any_of(self, s):
        """Match on any of the characters in the string s.  If the preceding element
        is a Not, invert the sense of the match."""
        charset = ''.join(map(RE.escape, s))
        if self.__ends_with_not():
            return RE(self.elements[:-1], "[^%s]" % charset)
        return RE(self, "[%s]" % charset)

    # repeat filters
    def zero_or_more(self):
        """The FOLLOWING element matches when repeated zero or more times"""
        return RE(self, Repeater(minimum=0, maximum=-1))

    def any_number_of(self):
        """Synonym for zero_or_more"""
        return self.zero_or_more()

    def zero_or_once(self):
        """The FOLLOWING element matches when repeated zero or once"""
        return RE(self, Repeater(minimum=0, maximum=1))

    def zero_or_one(self):
        """Synonym for zero_or_once"""
        return self.zero_or_once()

    def optional(self):
        """Synonym for zero_or_once"""
        return self.zero_or_once()

    def one_or_more(self):
        """The FOLLOWING element matches when repeated one or more times"""
        return RE(self, Repeater(minimum=1, maximum=-1))

    def at_least_one(self):
        """Synonym for one_or_more"""
        return self.one_or_more()

    def exactly(self, n):
        """The FOLLOWING element matches when repeated n times"""
        return RE(self, Repeater(minimum=n, maximum=n))

    def one(self):
        """Synonym for exactly(1)"""
        return self.exactly(1)

    def up_to(self, n):
        """The FOLLOWING element matches when repeated up to n times"""
        return RE(self, Repeater(minimum=0, maximum=n))

    def between(self, n, m):
        """The FOLLOWING element matches when repeated at least n times and at most m times"""
        return RE(self, Repeater(minimum=min(n, m), maximum=max(n, m)))

    # Convenience methods

    def dot(self):
        """Add a literal '.', escaped"""
        return RE(self, r'\.')

    def underscore(self):
        """Add a literal '_'"""
        return RE(self, '_')

    def dash(self):
        """Add a literal '-' - always escaped"""
        return RE(self, r'\-')

    def followed_by(self):
        """A no-op - may be included purely to make the fluent expression more readable"""
        return self

    def then(self):
        """A no-op - may be included purely to make the fluent expression more readable"""
        return self

    # Logical

    def not_a(self):
        """Add a Not element, that inverts the next applicable
        element.  Since not is a reserved word in Python, we
        use not_a."""
        return RE(self, Not())

    def not_an(self):
        """Synonym for not()"""
        return self.not_a()

    # Capturing
    def group(self, name=None):
        """Start a named or un-named group"""
        return RE(self, StartGroup(name=name))

    def start_group(self, name=None):
        """synonym for group"""
        return self.group(name=name)

    def end_group(self):
        return RE(self, EndGroup())

    # groupings of RE objects
    def any_re(self, *args):
        """Match on any of the args, which can be RE objects or strings"""
        return RE(self, '|'.join(x.as_string() if isinstance(x, RE) else unicode(x) for x in args))

# Unit tests go below here

import unittest


class SimpleTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().literal(u"hello").as_string(), u"hello")
        self.assertEqual(RE().start().end().as_string(), "^$")
        self.assertEqual(RE().start().literal("hello").end().as_string(), "^hello$")
        self.assertEqual(RE()
                         .alphanumeric().word_boundary().digit()
                         .as_string(),
                         r"\w\b\d")

        self.assertEqual(RE().any_of("abcdef").as_string(), r"[abcdef]")

        # Verify that all metacharacters are quoted
        self.assertEqual(RE().any_of(RE.metacharacters).as_string(),
                         "[%s]" % (RE.backslash + RE.backslash.join(RE.metacharacters)))

        r = RE().start().end().as_re()
        self.assertTrue(hasattr(r, "match") and hasattr(r, "search"))


class NotTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().digit().not_a().digit().as_string(), r"\d\D")
        self.assertEqual(RE().word_boundary().not_a().word_boundary().as_string(),
                         r"\b\B")
        self.assertEqual(RE().not_an().alphanumeric().digit().alphanumeric().as_string(),
                         r"\W\d\w")


class RepeatTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().zero_or_once().digit().as_string(), "\d?")
        self.assertEqual(RE().zero_or_one().digit().as_string(), "\d?")
        self.assertEqual(RE().zero_or_more().digits().as_string(), "\d*")
        self.assertEqual(RE().any_number_of().digits().as_string(), "\d*")
        self.assertEqual(RE().at_least_one().digit().as_string(), "\d+")
        self.assertEqual(RE().between(2, 5).digit().as_string(), "\d{2,5}")
        self.assertEqual(RE().between(5, 2).digit().as_string(), "\d{2,5}")


class GroupTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().start()
                         .group().any_number_of().alphanumeric().end_group()
                         .as_string(),
                         r"^(\w*)")
        self.assertEqual(RE()
                         .group().start_group().zero_or_more().alphanumeric().end_group().end_group()
                         .as_string(),
                         r"((\w*))")
        self.assertEqual(RE().start()
                         .group(name="abcd").any_number_of().alphanumeric().end_group()
                         .as_string(),
                         r"^(?P<abcd>\w*)")


class FormatErrorTests(unittest.TestCase):
    def runTest(self):
        self.assertRaises(FormatError, RE().end_group().start_group().at_least_one().digit().end_group().as_string)
        self.assertRaises(FormatError, RE().start_group().at_least_one().digit().end_group().end_group().as_string)


class Examples(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE()
                         .any_number_of().digits().literal('.').at_least_one().digit()
                         .as_string(),
                         r"\d*\.\d+")

        self.assertEqual(RE()
                         .any_number_of().digits().followed_by().dot().then().at_least_one().digit()
                         .as_string(),
                         r"\d*\.\d+")

        self.assertEqual(RE()
                         .up_to(8).alphanumerics().dot().group(name="ext").up_to(3).alphanumerics().end_group()
                         .as_string(),
                         r"\w{0,8}\.(?P<ext>\w{0,3})")

        #Match a US/Canadian phone number
        north_american_number_re = (RE().start()
                                    .literal('(').followed_by().exactly(3).digits().then().literal(')')
                                    .then().one().literal("-").then().exactly(3).digits()
                                    .then().one().dash().followed_by().exactly(4).digits().then().end()
                                    .as_string())

        number_re = re.compile(north_american_number_re)
        match = number_re.match("(123)-456-7890")
        self.assertIsNotNone(match)


