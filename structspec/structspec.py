#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
StructSpec: specify binary packet structures

StructSpec provides a language-independent, platform-neutral way
to specify the structures of binary packets and provide some basic
validation as well as output handlers in some common languages. It
is based on the JSON Schema standard (defined in IETF drafts at:
http://tools.ietf.org/html/draft-zyp-json-schema-04 and
http://tools.ietf.org/html/draft-fge-json-schema-validation-00 for
core and validation, respectively).
"""

from sys import exit
from argparse import ArgumentParser
try:
    from simplejson.decoder import JSONDecodeError
    from simplejson import load as loadJson
except ImportError:
    from json.decoder import JSONDecodeError
    from json import load as loadJson
try:
    from jsonschema.exceptions import ValidationError
    from jsonschema import validate as validateJson
except ImportError:
    try:
        from jsonspec.validators.exceptions import ValidationError
        from jsonspec.validators import load as loadValidator
        def validateJson(jsonObj, jsonSchema):
            validator = loadValidator(schema)
            validator.validate(sample)
    except ImportError:
        print("No supported JSON validation library found.")
        exit(1)
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
__version__ = '0.1'


def parseArguments(args=None):
    """
    Parse command-line arguments

    Examine command line and form and return an arguments structure
    that includes information about everything in it.

    Args:
        args (list): An optional set of command-line arguments used
                     for testing purposes.

    Returns:
        Dictionary of flags parsed from command line with their
        relevant arguments.

    Examples:
        >>> from argparse import Namespace
        >>> expectedResults = Namespace( \
                specification='specification.json', \
                languages=['Python', 'C'], \
                schema='structspec-schema.json', \
                test=False, verbose=False)
        >>> # Note that usually this is given no arguments so
        >>> # it'll just read from the command line.
        >>> # It's here given an empty list just for testing.
        >>> parser = parseArguments([])
        >>> parser == expectedResults
        True
        >>> expectedResults.verbose = True
        >>> parser = parseArguments(['--verbose'])
        >>> parser == expectedResults
        True
        >>> expectedResults.test = True
        >>> parser = parseArguments(['--test', '-v'])
        >>> parser == expectedResults
        True
        >>> expectedResults.specification = 'my.json'
        >>> expectedResults.test = expectedResults.verbose = False
        >>> parser = parseArguments(['--specification','my.json'])
        >>> parser == expectedResults
        True
        >>> expectedResults.schema = 's.json'
        >>> parser = parseArguments(['--schema', 's.json', '-s','my.json'])
        >>> parser == expectedResults
        True
        >>> expectedResults.specification = 'specification.json'
        >>> expectedResults.schema = 'structspec-schema.json'
        >>> # This next one displays help and exits; catch the exit
        >>> parser = parseArguments(['--help'])
        Traceback (most recent call last):
        SystemExit: 0
    """
    assert args is None or isinstance(args, list)
    # Parse command-line arguments
    parser = ArgumentParser(
        description="Process binary packet structure specifications. " + \
        "Given an input JSON file describing the format of a binary " + \
        "structure, validate it and output basic handlers in desired " + \
        "target languages."
    )
    defaultSpecification = 'specification.json'
    parser.add_argument(
        '--specification', '-s', default=defaultSpecification,
        nargs='?', const=defaultSpecification,
        help='Specification file defining binary packet formats. ' + \
        'By default this is called {}'.format(defaultSpecification)
    )
    defaultLanguageList = ['Python', 'C']
    acceptedLanguageList = ['Python', 'C']
    parser.add_argument(
        '--languages', '-l', default=defaultLanguageList, nargs='*',
        choices=acceptedLanguageList,
        help='Languages to output; {} by default.'.format(
            ' and '.join(defaultLanguageList))
    )
    parser.add_argument(
        '--test', action='store_true', help='Test program and exit.'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Make output more verbose.'
    )
    parser.add_argument('--version', action='version', version=__version__)
    defaultStructSpecSchema = 'structspec-schema.json'
    parser.add_argument(
        '--schema', default=defaultStructSpecSchema,
        nargs='?', const=defaultStructSpecSchema,
        help='JSON Schema file used to validate specification. ' + \
        'You probably do not need to change this.'
    )
    return parser.parse_args(args)


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
    if isinstance(err.args[0], int):
        errNum = err.args[0]
    else:
        errNum = 5
    exit(errNum)


if __name__ == "__main__":
    args = parseArguments()
    if not args.test:
        try:
            schemaFile = open(args.schema)
            schema = loadJson(schemaFile)
        except EnvironmentError as envErr:
            giveUp("Schema environment error", envErr)

        try:
            specificationFile = open(args.specification)
            specification = loadJson(specificationFile)
        except EnvironmentError as envErr:
            giveUp("Specification environment error", envErr)
        except JSONDecodeError as jsonErr:
            giveUp("Specification JSON decode error", jsonErr)
 
        try:
            if args.verbose:
                print("Validating specification.")
            validateJson(specification, schema)
            if args.verbose:
                print("Specification validated.")
        except ValidationError as valErr:
            giveUp("Validation error", valErr)
    else:
        import doctest
        doctest.testmod(verbose=args.verbose)

