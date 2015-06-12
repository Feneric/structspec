#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Common routines used across StructSpec

This file includes a handful of routines of general use that
are needed by multiple portions of structspec.
"""

from sys import exit
from os import linesep
from six import string_types
from zope.interface import directlyProvides
from interfaces import IOutputter

__line_len__ = 65
schemaVal = '/value'
typeSizes = {
    "char": 8,
    "signed char": 8,
    "unsigned char": 8,
    "short": 16,
    "signed short": 16,
    "unsigned short": 16,
    "short int": 16,
    "signed short int": 16,
    "unsigned short int": 16,
    "int": 32,
    "signed int": 32,
    "unsigned int": 32,
    "long": 32,
    "signed long": 32,
    "unsigned long": 32,
    "long int": 32,
    "signed long int": 32,
    "unsigned long int": 32,
    "long long": 64,
    "signed long long": 64,
    "unsigned long long": 64,
    "long long int": 64,
    "signed long long int": 64,
    "unsigned long long int": 64,
    "float": 32,
    "double": 64,
    "long double": 128,
    "bool": 16,
    "boolean": 8,
    "_Bool": 8,
    "int8_t": 8,
    "uint8_t": 8,
    "int16_t": 16,
    "uint16_t": 16,
    "int24_t": 24,
    "uint24_t": 24,
    "int32_t": 32,
    "uint32_t": 32,
    "int64_t": 64,
    "uint64_t": 64,
    "hollerith": 8,
    "string": 8,
    "str": 8,
    "pascal": 8,
    "pointer": 16,
    "void": 16,
    "padding": 8
}


def isStringType(typeName):
    """
    Determines whether or not the given type is a string.

    Given the name of the type returns a True if it is a
    string type or a False otherwise.

    Args:
        typeName (str): The name of the type to be checked.

    Returns:
        True if it is a string, False otherwise.

    Examples:
        >>> isStringType('string')
        True
        >>> isStringType('char')
        True
        >>> isStringType('hollerith')
        True
        >>> isStringType('pascal')
        True
        >>> isStringType('int')
        False
        >>> isStringType('float')
        False
        >>> isStringType('bool')
        False
    """
    return typeName in ('char', 'string', 'str', 'hollerith', 'pascal')


def isBooleanType(typeName):
    """
    Determines whether or not the given type is a boolean.

    Given the name of the type returns a True if it is a
    boolean type or a False otherwise.

    Args:
        typeName (str): The name of the type to be checked.

    Returns:
        True if it is a boolean, False otherwise.

    Examples:
        >>> isBooleanType('bool')
        True
        >>> isBooleanType('boolean')
        True
        >>> isBooleanType('_Bool')
        True
        >>> isBooleanType('char')
        False
        >>> isBooleanType('string')
        False
        >>> isBooleanType('int')
        False
        >>> isBooleanType('float')
        False
    """
    return typeName in ('bool', 'boolean', '_Bool')


def isPadding(typeName):
    """
    Determines whether or not the given type is padding.

    Given the name of the type returns a True if it is
    padding or a False otherwise.

    Args:
        typeName (str): The name of the type to be checked.

    Returns:
        True if it is padding, False otherwise.

    Examples:
        >>> isPadding('padding')
        True
        >>> isPadding('boolean')
        False
        >>> isPadding('char')
        False
        >>> isPadding('string')
        False
        >>> isPadding('int')
        False
        >>> isPadding('float')
        False
    """
    return typeName == 'padding'


def isFloatType(typeName):
    """
    Determines whether or not the given type is a float.

    Given the name of the type returns a True if it is a
    floating point type or a False otherwise.

    Args:
        typeName (str): The name of the type to be checked.

    Returns:
        True if it is a float, False otherwise.

    Examples:
        >>> isFloatType('float')
        True
        >>> isFloatType('double')
        True
        >>> isFloatType('long double')
        True
        >>> isFloatType('boolean')
        False
        >>> isFloatType('char')
        False
        >>> isFloatType('string')
        False
        >>> isFloatType('int')
        False
    """
    return typeName in ('float', 'double', 'long double')


def isIntegerType(typeName):
    """
    Determines whether or not the given type is a integer.

    Given the name of the type returns a True if it is a
    integer type or a False otherwise.

    Args:
        typeName (str): The name of the type to be checked.

    Returns:
        True if it is a integer, False otherwise.

    Examples:
        >>> isIntegerType('int')
        True
        >>> isIntegerType('short')
        True
        >>> isIntegerType('unsigned short')
        True
        >>> isIntegerType('long')
        True
        >>> isIntegerType('unsigned long')
        True
        >>> isIntegerType('long long')
        True
        >>> isIntegerType('uint8_t')
        True
        >>> isIntegerType('uint64_t')
        True
        >>> isIntegerType('float')
        False
        >>> isIntegerType('boolean')
        False
        >>> isIntegerType('char')
        False
        >>> isIntegerType('string')
        False
    """
    return typeName in typeSizes and not isStringType(typeName) and \
        not isFloatType(typeName) and not isBooleanType(typeName) \
        and not isPadding(typeName)


def isNonPortableType(typeName):
    """
    Determines whether or not the given type is unambiguous.

    Given the name of the type returns a True if it is an
    integer type with a size that varies across platforms.

    Args:
        typeName (str): The name of the type to be checked.

    Returns:
        True if a non-portable size, False otherwise.

    Examples:
        >>> isNonPortableType('int')
        True
        >>> isNonPortableType('short')
        True
        >>> isNonPortableType('unsigned short')
        True
        >>> isNonPortableType('long')
        True
        >>> isNonPortableType('unsigned long')
        True
        >>> isNonPortableType('long long')
        True
        >>> isNonPortableType('int8_t')
        False
        >>> isNonPortableType('uint16_t')
        False
        >>> isNonPortableType('uint32_t')
        False
        >>> isNonPortableType('str')
        False
    """
    return isIntegerType(typeName) and typeName not in (
        "int8_t", "uint8_t", "int16_t", "uint16_t",
        "int24_t", "uint24_t", "int32_t", "uint32_t",
        "int64_t", "uint64_t")


def getJsonPointer():
    """
    Gets a JSON Pointer resolver.

    Returns some sort of JSON Pointer resolver. As there are a
    few available in Python generally tries them in desired
    order.

    Returns:
        A function that can resolve a given JSON Pointer.

    Examples:
        >>> resolveJsonPointer = getJsonPointer()
        >>> callable(resolveJsonPointer)
        True
    """
    try:
        from jsonpointer import resolve_pointer as resolveJsonPointer
    except ImportError:
        try:
            from jsonspec.pointer import extract as resolveJsonPointer
        except ImportError:
            try:
                from json_pointer import Pointer as JsonPointer

                def resolveJsonPointer(jsonObj, jsonPointer):
                    return JsonPointer(jsonPointer).get(jsonObj)
            except ImportError:
                print("No supported JSON pointer library found.")
                exit(1)
    return resolveJsonPointer


def giveUp(category, err):
    """
    Aborts the program with a useful message.

    Given a message string and exception, displays the message plus
    exception string and exits, returning the exception error number.

    Args:
        category (str):  A brief string to prepend to the message.
        err (exception): The thrown exception.

    Examples:
        >>> bareException = BaseException('Ouch!')
        >>> giveUp('Complaint', bareException)
        Traceback (most recent call last):
        SystemExit: 5
        >>> envException = EnvironmentError(23, 'Crash.')
        >>> giveUp('System Report', envException)
        Traceback (most recent call last):
        SystemExit: 23
    """
    assert isinstance(category, str) and isinstance(err, BaseException)
    print("{}: {}".format(category, err))
    try:
        errNum = int(err.args[0])
    except (ValueError, IndexError):
        errNum = 5
    exit(errNum)


def writeOut(outFiles, outStr, prefix=''):
    """
    Writes a string to one or more files.

    Writes out the given string to the provided file(s)
    followed by a platform-appropriate end-of-line sequence.

    Args:
        outFiles (tuple or file): The target output file or
                                  a tuple of output files.
        outStr (str):             The string to output.
        prefix (str):             Optional string to use as
                                  a prefix.

    Examples:
        >>> from StringIO import StringIO
        >>> out1 = StringIO()
        >>> out2 = StringIO()
        >>> writeOut(out1, 'test')
        >>> out1.getvalue().rstrip()
        'test'
        >>> writeOut((out1, out2), 'test', 'this is a ')
        >>> out2.getvalue().rstrip()
        'this is a test'
        >>> out1.getvalue()[:4]
        'test'
        >>> out1.getvalue()[-8:-1]
        ' a test'
    """
    assert hasattr(outFiles, 'write') or (isinstance(outFiles, tuple)
        and all([hasattr(outFile, 'write') for outFile in outFiles]))
    assert isinstance(outStr, string_types) and \
        isinstance(prefix, string_types)
    if hasattr(outFiles, 'write'):
        outFiles = [outFiles]
    outStr = '{}{}'.format(prefix, outStr)
    if not outStr.endswith(linesep):
        outStr = '{}{}'.format(outStr, linesep)
    for outFile in outFiles:
        outFile.write(outStr.encode('utf8'))
directlyProvides(writeOut, IOutputter)


def writeOutBlock(outFiles, outStr, prefix=''):
    """
    Writes a long string to one or more files in lines.

    Writes out the given string to the provided file(s)
    breaking it up into individual lines separated by
    appropriate end-of-line sequences.

    Args:
        outFiles (file or tuple): The target output file or
                                  a tuple of output files.
        outStr (str):             The string to output.
        prefix (str):             Optional string to use
                                  as a prefix.

    Examples:
        >>> from StringIO import StringIO
        >>> out1 = StringIO()
        >>> out2 = StringIO()
        >>> writeOut(out2, 'test', 'a ')
        >>> out2.getvalue().rstrip()
        'a test'
        >>> writeOut((out1, out2), 'test', 'this is a ')
        >>> out1.getvalue().rstrip()
        'this is a test'
        >>> out2.getvalue()[:6]
        'a test'
        >>> out2.getvalue()[-8:-1]
        ' a test'
    """
    assert hasattr(outFiles, 'write') or (isinstance(outFiles, tuple)
        and all([hasattr(outFile, 'write') for outFile in outFiles]))
    assert isinstance(outStr, str) and isinstance(prefix, str)
    lines = []
    words = outStr.split()
    startWordNum = wordNum = 0
    while wordNum < len(words):
        lineLen = 0
        while wordNum < len(words):
            if lineLen + len(words[wordNum]) > __line_len__:
                break
            lineLen += len(words[wordNum])
            wordNum += 1
        lines.append('{}{}{}'.format(prefix,
                     ' '.join(words[startWordNum:wordNum]),
                     linesep))
        startWordNum = wordNum
    writeOut(outFiles, ''.join(lines).encode('utf8'))
directlyProvides(writeOutBlock, IOutputter)


# Execute the following when run from the command line.
if __name__ == "__main__":
    import doctest
    doctest.testmod()
