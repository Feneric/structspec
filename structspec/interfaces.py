# -*- coding: utf-8 -*-
"""
Interfaces for StructSpec

Herein one will find all the interfaces defined for StructSpec.
In particular the interface for language definitions is provided.
"""

from zope.interface import Interface, Attribute

# PyLint isn't too smart about ZOPE style interfaces.  Thus we'll disable a
# few features that would otherwise require us to make it less readable.

#pylint: disable=R0903
#pylint: disable=W0232
#pylint: disable=E0211
#pylint: disable=E0213

# Public API Interfaces


class ILanguage(Interface):
    """
    An entity that defines language support

    Interface for anything capable of writing language files.
    """
    name = Attribute("""The name of the language, a string""")
    filenameExtension = Attribute("""A string or tuple of strings"""
        """representing filename extensions used by the language""")

    def outputForLanguage(specification, options):
        """Outputs the file(s) used by the language"""


class IOutputter(Interface):
    """
    Something that outputs data

    Interface for any entity capable of writing out data.
    """

    def __call__(outFiles, outStr, prefix):
        """Writes outStr to outFile(s) prefixed with prefix"""

