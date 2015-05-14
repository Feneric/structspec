#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Common routines used across StructSpec

This file includes a handful of routines of general use that
are needed by multiple portions of structspec.
"""

from sys import exit
from os import linesep
from zope.interface import directlyProvides
from interfaces import IOutputter

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
    """
    return not isStringType(typeName) and not isFloatType(typeName) and \
           not isBooleanType(typeName)


def getJsonPointer():
    """
    Gets a JSON Pointer resolver.

    Returns some sort of JSON Pointer resolver. As there are a
    few available in Python generally tries them in desired
    order.

    Returns:
        A function that can resolve a given JSON Pointer.
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
    """
    assert hasattr(outFiles, 'write') or (isinstance(outFiles, tuple)
        and all([hasattr(outFile, 'write') for outFile in outFiles]))
    assert isinstance(outStr, str) and isinstance(prefix, str)
    if hasattr(outFiles, 'write'):
        outFiles = [outFiles]
    for outFile in outFiles:
        outFile.write('{}{}{}'.format(prefix, outStr, linesep))
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
            ' '.join(words[startWordNum:wordNum])), linesep)
        startWordNum = wordNum
    writeOut(outFiles, ''.join(lines))
directlyProvides(writeOutBlock, IOutputter)


# Execute the following when run from the command line.
if __name__ == "__main__":
    import doctest
    doctest.testmod()

