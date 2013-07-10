"""
Fluent functional interface for grimace.

The target use case is something like:

    from grimace.fluent import RE    # (bad practice, you wouldn't normally do this)
    my_re = RE().start().literal('/blog/').capture_named('asset_id',zero_or_more(digit()))

"""
__author__ = 'BenL'

import types

class RE(object):
    """Class that represents a regexp string being assembled.
    To support the fluent syntax, start with an instance of this class
    and then call methods on it, each of which will yield a new instance
    that is extended.
    When done, a str() will return the regexp string.
    """

    def __init__(self, *args):
        """
        Create a new RE - the core of an RE is a list of substrings, which
        grows with each addition (or has the tail element modified in some cases)
        until stringified at the end.
        If args are supplied: the elements list for this instance is built up by adding
        the elements lists from any args that are instances of this class, and any strings
        or unicode strings.
        """
        def reducer(elements, arg):
            """If arg is a string, return elements with the string appended.
            If arg is an iterable, return elements with the elements of arg appended.
            If arg is an instance of this class, return elements with the elements of that
            instance appended.
            """
            # Note that while type checking is generally evil, we do it here to ensure that
            # we consume only strings and lists of strings.
            if type(arg) in types.StringTypes:
                return elements + arg
            elif isinstance(arg, RE):
                return elements + arg.elements
            try:
                return elements + [x for x in arg if type(x) in types.StringTypes]
            except TypeError:
                # raised if arg is not iterable, in which case we silently ignore it
                pass

        self.elements = reduce(reducer, args) if args else []

    def __unicode__(self):
        """Return the regexp as Unicode, decoding any strings from ascii if required."""
        return u"".join((x if type(x)==types.UnicodeType else x.decode('ascii') for x in self.elements))

    def __str__(self):
        """Return the regexp as a string, encoding any unicode elements to ascii if required, which means there
        may be an EncodingError raised."""
        return "".join((x if type(x)==types.StringType else x.encode('ascii') for x in self.elements))

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
        """Adds a digit '\d' specifier to the regexp"""
        return RE(self, r'\d')

    def non_digit(self):
        """Adds a nondigit '\D' specifier to the regexp"""
        return RE(self, r'\D')

    def whitespace(self):
        """Adds a whitespace '\s' specifier to the regexp"""
        return RE(self, r'\s')

    def non_whitespace(self):
        """Adds a non-whitespace '\S' specifier to the regexp"""
        return RE(self, r'\S')

    def alphanumeric(self):
        """Adds an alphanumeric '\w' specifier to the regexp - this matches
        any of a-z, A-Z or 0-9"""
        return RE(self, r'\w')

    def non_alphanumeric(self):
        """Adds an non-alphanumeric '\W' specifier to the regexp - this matches
        anything except a-z, A-Z or 0-9"""
        return RE(self, r'\W')

    def any_of(self, s):
        """Match on any of the characters in the string s"""
        return RE(self, '[', map(RE.escape, s), ']')

    # repeat filters
    def zero_or_more(self):
        """The PREVIOUS element matches when repeated zero or more times"""
        #TODO - build a way to do this as a prefix call not a postfix call
        return RE(self, r'*')

    def zero_or_once(self):
        """The PREVIOUS element matches when repeated zero or once"""
        #TODO - build a way to do this as a prefix call not a postfix call
        return RE(self, r'?')

    def one_or_more(self):
        """The PREVIOUS element matches when repeated one or more times"""
        #TODO - build a way to do this as a prefix call not a postfix call
        return RE(self, r'+')

    def exactly(self, n):
        """The PREVIOUS element matches when repeated n times"""
        #TODO - build a way to do this as a prefix call not a postfix call
        return RE(self, r'{%d,%d' % (n, n))

    def between(self, n, m):
        """The PREVIOUS element matches when repeated at least n times and at most m times"""
        #TODO - build a way to do this as a prefix call not a postfix call
        return RE(self, r'{%d,%d' % (n, m))

    # groupings of RE objects
    def any_re(self, *args):
        """Match on any of the args, which can be RE objects or strings"""
        return RE(self, '|'.join(unicode(x) for x in args))

