#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests structspec

These tests may all be executed by running "setup.py test" or executing
this file directly.
"""
import unittest

if __name__ == '__main__':
    from sys import path
    from os import chdir, getcwd
    from os.path import normpath, dirname
    path.append('structspec')
    chdir(normpath(join(getcwd(), dirname(__file__), '..', '..')))
    from structspec import *
else:
    from ..structspec import *


class TestStructSpec(unittest.TestCase):
    """
    Define our structspec tests.
    """
    print("Not yet implemented.")


if __name__ == '__main__':
    # When executed from the command line, run all the tests via unittest.
    from unittest import main
    main()

