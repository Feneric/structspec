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


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(structspec))
    tests.addTests(DocTestSuite(structspec.common))
    tests.addTests(DocTestSuite(structspec.languages))
    return tests


class TestStructSpec(unittest.TestCase):
    """
    Define our structspec tests.
    """
    print("Not yet implemented.")

    def test_interface(self):
        """
        Test that it satisfies the appropriate interface.
        """
        for outputter in (structspec.common.writeOut,
                          structspec.common.writeOutBlock):
            verifyObject(structspec.interfaces.IOutputter, outputter)


if __name__ == '__main__':
    # When executed from the command line, run all the tests via unittest.
    from unittest import main
    main()

