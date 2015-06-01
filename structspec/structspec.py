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
from os.path import join
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
from common import giveUp, isNonPortableType, getJsonPointer
# Fetch all language modules without knowing a priori what's available
import languages
from languages import *
for supportedLang in languages.__all__:
    import_module('structspec.languages.' + supportedLang)
__langModTups__ = getmembers(languages, predicate=ismodule)
langModules = dict([(langMod[1].name, langMod[1])
                   for langMod in __langModTups__])

# Get a workable JSON pointer resolver from whichever library
resolveJsonPointer = getJsonPointer()

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
                include=False, test=False, verbose=False)
        >>> # Note that usually this is given no arguments so
        >>> # it'll just read from the command line.
        >>> # It's here given an empty list just for testing.
        >>> parseAgs = parseArguments([])
        >>> parseAgs == expectedResults
        True
        >>> expectedResults.verbose = True
        >>> expectedResults.include = True
        >>> parseAgs = parseArguments(['--verbose', '--include'])
        >>> parseAgs == expectedResults
        True
        >>> expectedResults.include = False
        >>> expectedResults.test = True
        >>> parseAgs = parseArguments(['--test', '-v'])
        >>> parseAgs == expectedResults
        True
        >>> expectedResults.specification = 'my.json'
        >>> expectedResults.test = expectedResults.verbose = False
        >>> parseAgs = parseArguments(['--specification','my.json'])
        >>> parseAgs == expectedResults
        True
        >>> expectedResults.schema = 's.json'
        >>> parseAgs = parseArguments(['--schema', 's.json', '-s','my.json'])
        >>> parseAgs == expectedResults
        True
        >>> expectedResults.specification = 'specification.json'
        >>> expectedResults.schema = 'structspec-schema.json'
        >>> # This next one displays help and exits; catch the exit
        >>> parseAgs = parseArguments(['--help'])
        Traceback (most recent call last):
        SystemExit: 0
    """
    assert args is None or isinstance(args, list)
    # Parse command-line arguments
    parser = ArgumentParser(
        description="Process binary packet structure specifications. " +
        "Given an input JSON file describing the format of a binary " +
        "structure, validate it and output basic handlers in desired " +
        "target languages."
    )
    defaultSpecification = 'specification.json'
    parser.add_argument(
        '--specification', '-s', default=defaultSpecification,
        nargs='?', const=defaultSpecification,
        help='Specification file defining binary packet formats. ' +
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
    defaultStructSpecSchema = join('structspec', 'structspec-schema.json')
    parser.add_argument(
        '--schema', default=defaultStructSpecSchema,
        nargs='?', const=defaultStructSpecSchema,
        help='JSON Schema file used to validate specification. ' +
        'You probably do not need to change this.'
    )
    return parser.parse_args(args)


def checkJsonPointer(specification, jsonPointer):
    """
    Verifies that the given JSON Pointer can be resolved.

    Given a string, determine if it is a JSON Pointer and
    if so try to resolve it. If it does not need to be
    resolved or resolves successfully, return True.

    Args:
        specification (dict): The JSON structure in
                              which to resolve the
                              JSON Pointer.
        jsonPointer (str):    A string that may be a
                              JSON Pointer.

    Returns:
        True if it is not a JSON Pointer or is one and
        resolves, False otherwise.

    Examples:
        >>> checkJsonPointer({}, '/')
        True
        >>> checkJsonPointer({}, '#/')
        False
        >>> checkJsonPointer({'unu': 1}, '#/unu')
        True
        >>> checkJsonPointer({'unu':1}, '#/nul')
        False
    """
    assert isinstance(specification, dict)
    assert isinstance(jsonPointer, str)
    if jsonPointer.startswith('#/'):
        try:
            resolveJsonPointer(specification, jsonPointer[1:])
        except:
            return False
    return True


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
            # If verbose, provide good practice checks
            if 'endianness' not in specification:
                print('A default endianness is recommended.')
            elif specification['endianness'] == 'native':
                print('A portable default endianness is recommended.')
            # Basic enumeration checks
            if 'enums' in specification:
                for enumName, enum in specification['enums'].items():
                    if 'type' not in enum:
                        print('No type for enumeration {}.'.format(
                              enumName))
                    elif not checkJsonPointer(specification, enum['type']):
                        print('{} has bad JSON Pointer.'.format(enumName))
            # Basic packet checks
            for packetName, packet in specification['packets'].items():
                if packet.get('endianness', None) == 'native':
                    print('Packet {} has a non-portable endianness.'.format(
                          packetName))
                for structureName, structure in packet['structure'].items():
                    if isNonPortableType(structure['type']):
                        print('Non-portable type for {} ({}).'.format(
                              packetName, structureName))
                    if structure.get('endianness', None) == 'native':
                        print('{} ({}) has a non-portable endianness.'.format(
                              packetName, structureName))
                    for attr in ('type', 'max', 'min', 'member',
                                 'count', 'size'):
                        if attr in structure and \
                                not checkJsonPointer(specification,
                                                     structure[attr]):
                            print('{} ({} {}) has bad JSON Pointer.'.format(
                                  packetName, structureName, attr))
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
def main():
    """
    The main routine when run from the command line.

    Executes structspec interactively from the command line.
    """
    args = parseArguments()
    if not args.test:
        specification, schema, options = loadAndValidateInputs(args)
        for language in args.languages:
            langModules[language].outputForLanguage(specification, options)
    else:
        import doctest
        doctest.testmod(verbose=args.verbose)


if __name__ == "__main__":
    main()
