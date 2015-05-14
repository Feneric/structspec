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
from os import linesep
from collections import OrderedDict
from argparse import ArgumentParser, Namespace
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
from importlib import import_module
from inspect import getmembers, ismodule
from zope.interface import directlyProvides
from common import giveUp
# Fetch all language modules without knowing a priori what's available
import languages
for supportedLang in languages.__all__:
   import_module('languages.' + supportedLang)
__langModTups__ = getmembers(languages, predicate=ismodule)
langModules = dict([(langMod[1].name, langMod[1])
    for langMod in __langModTups__])
from interfaces import IOutputter

__version__ = '0.1'
__line_len__ = 65


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
    defaultLanguageList = langModules.keys()
    writtenLanguageList = ', '.join(defaultLanguageList[:-1])
    oxfordComma = ',' if len(defaultLanguageList) > 2 else ''
    writtenLanguageList = '{}{} and {}'.format(writtenLanguageList,
                                               oxfordComma,
                                               defaultLanguageList[-1])
    helpStr = 'Languages to output; {} by default. '.format(
        writtenLanguageList) + \
        'Please note that the C option provides combined C/C++ support.'
    parser.add_argument(
        '--languages', '-l', default=defaultLanguageList, nargs='*',
        choices=langModules.keys(), help=helpStr
    )
    parser.add_argument(
        '--include', '-i', action='store_true',
        help='Include identifier within individual packets.'
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


def loadAndValidateInputs(args):
    """
    Loads the specification and schema and validates the former.

    Based on the given command-line arguments loads the
    appropriate specification and schema files, converts them
    from JSON, and performs a JSON Schema validation of the
    specification.

    Args:
        args (Namespace): The command-line arguments to use.

    Returns:
        A tuple containing the specification object (converted
        from JSON), the schema object (converted from JSON),
        and a dictionary of options parsed from the command line.
    """
    assert isinstance(args, Namespace)

    try:
        schemaFile = open(args.schema)
        schema = loadJson(schemaFile)
    except EnvironmentError as envErr:
        giveUp("Schema environment error", envErr)

    try:
        specificationFile = open(args.specification)
        specification = loadJson(specificationFile,
                                 object_pairs_hook=OrderedDict)
    except EnvironmentError as envErr:
        giveUp("Specification environment error", envErr)
    except JSONDecodeError as jsonErr:
        giveUp("Specification JSON decode error", jsonErr)

    try:
        if args.verbose:
            print("Validating specification...")
        validateJson(specification, schema)
        if args.verbose:
            print("Specification validated.")
            # Put in some extra checks here; look for missing
            # default endianess, missing types on enumerations,
            # ambiguous type definitions, etc.
    except ValidationError as valErr:
        giveUp("Validation error", valErr)

    options = {
        'includeIdentifier': args.include,
        'languages': args.languages,
        'schemaName': args.schema,
        'specificationName': args.specification,
        'verbose': args.verbose
    }
    return (specification, schema, options)


# Execute the following when run from the command line.
if __name__ == "__main__":
    args = parseArguments()
    if not args.test:
        specification, schema, options = loadAndValidateInputs(args)
        for language in args.languages:
            langModules[language].outputForLanguage(specification, options)
    else:
        import doctest
        doctest.testmod(verbose=args.verbose)

