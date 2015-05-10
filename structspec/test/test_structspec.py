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

if __name__ == '__main__':
    from sys import path
    from os import chdir, getcwd
    from os.path import normpath, dirname
    path.append('structspec')
    path.append('.')
    chdir(normpath(join(getcwd(), dirname(__file__), '..', '..')))
    from structspec import *
    import structspec
else:
    from ..structspec import *
    from structspec import structspec


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(structspec))
    return tests


class TestStructSpec(unittest.TestCase):
    """
    Define our structspec tests.
    """
    print("Not yet implemented.")


if __name__ == '__main__':
    # When executed from the command line, run all the tests via unittest.
    from unittest import main
    main()

