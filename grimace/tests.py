# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import re
import unittest
from nine import str
from grimace import RE, FormatError


class BaseTests(unittest.TestCase):
    def runTest(self):
        # Verify that the result of calling an RE is a reference to that RE
        r = RE()
        self.assertEqual(r, r())


class SimpleTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().literal("hello").as_string(), "hello")
        self.assertEqual(RE().start.end().as_string(), "^$")
        self.assertEqual(str(RE().start.end()), "^$")
        self.assertEqual(str(RE().start.end()), "^$")
        self.assertEqual(RE().start().literal("hello").end.as_string(), "^hello$")
        self.assertEqual(RE()
                         .alphanumeric().word_boundary().digit()
                         .as_string(),
                         r"\w\b\d")

        self.assertEqual(RE().start.zero_or_more.of.any_character.end.as_string(),
                         r'^.*$')

        self.assertEqual(RE().any_of("abcdef").as_string(), r"[abcdef]")

        # Verify that all metacharacters are quoted
        self.assertEqual(RE().any_of(RE.metacharacters).as_string(),
                         "[%s]" % (RE.backslash + RE.backslash.join(RE.metacharacters)))

        r = RE().start.end.as_re()
        self.assertTrue(hasattr(r, "match") and hasattr(r, "search"))

        self.assertEqual(RE().dot.as_string(), r"\.")
        r1 = RE().dot
        r2 = RE().dot
        self.assertNotEqual(r1, r2)

        identifier_start_chars = RE().regex("[a-zA-Z_]")
        identifier_chars = RE().regex("[a-zA-Z0-9_]")

        self.assertEqual(RE().one_or_more.of(identifier_start_chars)
                         .followed_by.zero_or_more(identifier_chars)
                         .as_string(),
                         r"[a-zA-Z_]+[a-zA-Z0-9_]*")

        self.assertEqual(str(RE().anything), r'.*')
        self.assertEqual(str(RE().non_greedy.anything), r'.*?')

        nlr = RE().newline
        self.assertEqual(str(nlr), r'\\n')
        assert nlr.as_re().match(r"\n")

        tlr = RE().tab
        self.assertEqual(str(tlr), r'\\t')
        assert tlr.as_re().match(r"\t")


class NotTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().digit.not_a.digit.as_string(), r"\d\D")
        self.assertEqual(RE().word_boundary.not_a.word_boundary.as_string(),
                         r"\b\B")
        self.assertEqual(RE().not_an.alphanumeric.then.digit.followed_by.alphanumeric.as_string(),
                         r"\W\d\w")


class RepeatTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().zero_or_once().digit().as_string(), "\d?")
        self.assertEqual(RE().non_greedy.zero_or_one.digit.as_string(), "\d??")
        self.assertEqual(RE().zero_or_one.digit.as_string(), "\d?")
        self.assertEqual(RE().zero_or_more().digits().as_string(), "\d*")
        self.assertEqual(RE().non_greedy.zero_or_more.digits.as_string(), "\d*?")
        self.assertEqual(RE().any_number_of.digits.as_string(), "\d*")
        self.assertEqual(RE().one.digit.as_string(), "\d{1,1}")
        self.assertEqual(RE().one.of.any_character.as_string(), ".{1,1}")
        self.assertEqual(RE().one.of_an.alpha.as_string(), "[a-zA-Z]{1,1}")
        self.assertEqual(RE().non_greedy.one.digit.as_string(), "\d{1,1}")  # not affected by greediness
        self.assertEqual(RE().at_least_one().digit().as_string(), "\d+")
        self.assertEqual(RE().non_greedy.at_least_one.digit.as_string(), "\d+?")
        self.assertEqual(RE().between(2, 5).digit().as_string(), "\d{2,5}")
        self.assertEqual(RE().non_greedy.between(25, 20).digit().as_string(), "\d{20,25}")
        self.assertEqual(RE().between(5, 2).digit().as_string(), "\d{2,5}")


class GroupTests(unittest.TestCase):
    def runTest(self):
        self.assertEqual(RE().start()
                         .group.at_least_one.alphanumeric.end_group.then.optional.whitespace
                         .as_string(),
                         r"^(\w+)\s?")
        self.assertEqual(RE().start()
                         .named_group("id").at_least_one.alphanumeric.end_group.then.optional.whitespace
                         .as_string(),
                         r"^(?P<id>\w+)\s?")
        self.assertEqual(RE()
                         .group.start_group().zero_or_more.alphanumerics.end_group.end_group()
                         .as_string(),
                         r"((\w*))")
        self.assertEqual(RE().start()
                         .named_group(name="abcd").any_number_of().alphanumeric().end_group()
                         .as_string(),
                         r"^(?P<abcd>\w*)")
        self.assertEqual(RE().start()
                         .start_named_group(name="abcd").any_number_of().alphanumeric().end_group()
                         .as_string(),
                         r"^(?P<abcd>\w*)")


class FormatErrorTests(unittest.TestCase):
    def runTest(self):
        self.assertRaises(FormatError, RE().end_group().start_group().at_least_one().digit().end_group().as_string)
        self.assertRaises(FormatError, RE().start_group().at_least_one().digit().end_group().end_group().as_string)


class Examples(unittest.TestCase):
    def test_any_of(self):
        r = RE().any_of('0123456789-.()abcdefghijklmnopqrstuvwxyz')
        re.compile(str(r))  # should not raise

    def test_examples(self):
        self.assertEqual(RE()
                         .any_number_of().digits().literal('.').at_least_one().digit()
                         .as_string(),
                         r"\d*\.\d+")

        self.assertEqual(RE()
                         .any_number_of.digits.followed_by.dot.then.at_least_one.digit()
                         .as_string(),
                         r"\d*\.\d+")

        self.assertEqual(RE()
                         .any_number_of.digits.followed_by.a.dot.then.at_least_one.digit()
                         .as_string(),
                         r"\d*\.{1,1}\d+")

        self.assertEqual(RE()
                         .any_number_of.digits.followed_by.an_optional.dot.then.at_least_one.digit
                         .as_string(),
                         r"\d*\.?\d+")

        self.assertEqual(RE()
                         .up_to(8).alphanumerics().dot().named_group(name="ext").up_to(3).alphanumerics().end_group()
                         .as_string(),
                         r"\w{0,8}\.(?P<ext>\w{0,3})")

        # Match a US/Canadian phone number
        north_american_number_re = (RE().start
                                    .literal('(').followed_by.exactly(3).digits().then.literal(')')
                                    .then.one().literal("-").then.exactly(3).digits()
                                    .then.one().dash().followed_by.exactly(4).digits().then.end
                                    .as_string())

        number_re = re.compile(north_american_number_re)
        match = number_re.match("(123)-456-7890")
        assert match
