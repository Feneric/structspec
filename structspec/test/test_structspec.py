#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests structspec

These tests may all be executed by running "setup.py test" or executing
this file directly.
"""
import unittest
from doctest import DocTestSuite
from os.path import join
from importlib import import_module
from zope.interface.verify import verifyObject

if __name__ == '__main__':
    from sys import path
    from os import chdir, getcwd
    from os.path import normpath, dirname
    path.append('.')
    chdir(normpath(join(getcwd(), dirname(__file__), '..', '..')))
import structspec
import structspec.common
import structspec.interfaces
import structspec.languages
import structspec.languages.c
import structspec.languages.python


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(structspec))
    tests.addTests(DocTestSuite(structspec.common))
    tests.addTests(DocTestSuite(structspec.languages))
    tests.addTests(DocTestSuite(structspec.languages.c))
    tests.addTests(DocTestSuite(structspec.languages.python))
    return tests


class TestStructSpec(unittest.TestCase):
    """
    Define our structspec tests.
    """
    print("Not yet implemented.")

    def test_write_interfaces(self):
        """
        Test that outputters all satisfy the appropriate interface.
        """
        for outputter in (structspec.common.writeOut,
                          structspec.common.writeOutBlock):
            verifyObject(structspec.interfaces.IOutputter, outputter)

    def test_language_interfaces(self):
        """
        Test that the language modules all satisfy the proper interface.
        """
        for langModule in (structspec.languages.c,
                           structspec.languages.python):
            verifyObject(structspec.interfaces.ILanguage, langModule)


if __name__ == '__main__':
    # When executed from the command line, run all the tests via unittest.
    from unittest import main
    main()

