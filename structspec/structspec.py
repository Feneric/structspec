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
from os.path import basename
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
__line_len__ = 65
__accepted_languages__ = ['Python', 'C']
__schema_val__ = '/value'
__type_sizes__ = {
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
    "string": 8
}


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
    defaultLanguageList = __accepted_languages__
    writtenLanguageList = ', '.join(defaultLanguageList[:-1])
    writtenLanguageList = '{}, and {}'.format(writtenLanguageList,
                                              defaultLanguageList[-1])
    helpStr = 'Languages to output; {} by default. '.format(
        writtenLanguageList) + \
        'Please note that the C option provides combined C/C++ support.'
    parser.add_argument(
        '--languages', '-l', default=defaultLanguageList, nargs='*',
        choices=__accepted_languages__, help=helpStr
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
    try:
        errNum = int(err.args[0])
    except (ValueError, IndexError):
        errNum = 5
    exit(errNum)


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
        from JSON) and the schema object (converted from JSON).
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
    except ValidationError as valErr:
        giveUp("Validation error", valErr)

    return (specification, schema)


def writeOut(outFile, outStr, prefix=''):
    """
    Writes a string to a file.

    Writes out the given string to the provided file followed
    by a platform-appropriate end-of-line sequence.

    Args:
        outFile (file): The target output file.
        outStr (str):   The string to output.
        prefix (str):   Optional string to use as a prefix.
    """
    assert hasattr(outFile, 'write')
    assert isinstance(outStr, str) and isinstance(prefix, str)
    outFile.write('{}{}{}'.format(prefix, outStr, linesep))


def writeOutBlock(outFile, outStr, prefix=''):
    """
    Writes a long string to a file in lines.

    Writes out the given string to the provided file breaking
    it up into individual lines separated by appropriate
    end-of-line sequences.

    Args:
        outFile (file): The target output file.
        outStr (str):   The string to output.
        prefix (str):   Optional string to use as a prefix.
    """
    assert hasattr(outFile, 'write')
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
    writeOut(outFile, ''.join(lines))


def outputC(specification, outFile):
    """
    Outputs C header file.

    Given the specification construct a valid C header
    file that describes all the binary packets.

    Args:
        specification (dict): The specification object.
        outFile (file):       A file-like object to which
                              to save the header.
    """
    assert isinstance(specification, dict)
    assert hasattr(outFile, 'write')
    defName = "STRUCTSPEC_{}_H".format(specification['id'].upper())
    writeOut(outFile, '#ifndef {}'.format(defName))
    writeOut(outFile, '#define {}'.format(defName))
    writeOut(outFile, '#ifdef __cplusplus')
    writeOut(outFile, 'extern "C"')
    writeOut(outFile, '{')
    writeOut(outFile, '#endif /* __cplusplus */')
    writeOut(outFile, '')
    writeOut(outFile, '/*')
    prefix = ' * '
    writeOut(outFile, specification['title'], prefix)
    if 'description' in specification:
        writeOut(outFile, ' *')
        writeOutBlock(outFile, specification['description'], prefix)
    for tag in ('version', 'date', 'author', 'documentation', 'metadata'):
        if tag in specification:
            writeOut(outFile, ' *')
            writeOut(outFile, '{}: {}'.format(tag.title(),
                                              specification[tag]),
                     prefix)
    writeOut(outFile, ' */')
    writeOut(outFile, '')
    writeOut(outFile, '#include <stdint.h>')
    writeOut(outFile, '')
    for enumerationName, enumeration in specification['enums'].items():
        writeOut(outFile, '/*')
        if 'title' in enumeration:
           writeOut(outFile, enumeration['title'], ' * ')
        else:
           writeOut(outFile, enumerationName, ' * ')
        if 'description' in enumeration:
            writeOut(outFile, ' *')
            writeOutBlock(outFile, enumeration['description'], ' * ')
        writeOut(outFile, ' */')
        if enumeration.get('preprocessor', False):
            for optionName, option in enumeration['options'].items():
                line = []
                line.append('#define ')
                line.append(optionName)
                if 'value' in option:
                    line.append(' {}'.format(option['value']))
                if 'title' in option:
                    line.append(' /* {} */'.format(option['title']))
                writeOut(outFile, ''.join(line))
        else:
            writeOut(outFile, "typedef enum {")
            lastOption = enumeration['options'].keys()[-1]
            for optionName, option in enumeration['options'].items():
                line = []
                line.append(optionName)
                if 'value' in option:
                    line.append(' = {}'.format(option['value']))
                if 'title' in option:
                    line.append(' /* {} */'.format(option['title']))
                if optionName != lastOption:
                    line.append(',')
                writeOut(outFile, ''.join(line), '  ')
            writeOut(outFile, "}} {}".format(enumerationName))
        writeOut(outFile, '')
    for packetName, packet in specification['packets'].items():
        writeOut(outFile, "typedef struct {")
        for structureName, structure in packet['structure'].items():
            line = []
            if structure['type'].startswith('#/'):
                 typeName = structure['type'][structure['type'].rfind('/') + 1:]
            else:
                 typeName = structure['type']
            line.append(typeName)
            line.append(' ')
            line.append(structureName)
            if 'count' in structure:
                if structure['count'].startswith('#/'):
                    countLabel = structure['count'][:-len(__schema_val__)]
                    countLabel = countLabel[countLabel.rfind('/') + 1:]
                else:
                    countLabel = structure['count']
                line.append('[{}]'.format(countLabel))
            if 'size' in structure:
                if structure['size'].startswith('#/'):
                    sizeLabel = structure['size'][:-len(__schema_val__)]
                    sizeLabel = sizeLabel[sizeLabel.rfind('/') + 1:]
                    sizeInBits = resolveJsonPointer(specification,
                                                    structure['size'][1:])
                else:
                    sizeLabel = structure['size']
                    try:
                        sizeInBits = int(sizeLabel)
                    except ValueError:
                        sizeInBits = 0
                if sizeInBits != __type_sizes__.get(typeName, -1):
                    line.append(' : {}'.format(sizeLabel))
            if 'title' in structure:
                line.append(' /* {} */'.format(structure['title']))
            line.append(';')
            writeOut(outFile, ''.join(line), '  ')
        writeOut(outFile, "}} {}".format(packetName))
        writeOut(outFile, '')
    writeOut(outFile, '#ifdef __cplusplus')
    writeOut(outFile, '}')
    writeOut(outFile, '#endif /* __cplusplus */')
    writeOut(outFile, '#endif /* {} */'.format(defName))


def outputPython(specification, outFile):
    """
    Outputs Python struct file.

    Given the specification construct a valid Python struct
    file that describes all the binary packets.

    Args:
        specification (dict): The specification object.
        outFile (file):       A file-like object to which
                              to save the struct code.
    """
    assert isinstance(specification, dict)
    assert hasattr(outFile, 'write')


def outputForLanguage(specification, language, args):
    """
    Outputs handler files for given language.

    Creates files to process given specification in given 
    programming language.  Bases output file names on given
    input specification file.

    Args:
        specification (dict): The specification object.
        language (str):       The target output language.
        args (Namespace):     Command-line options.
    """
    assert isinstance(specification, dict)
    assert isinstance(language, str)
    assert isinstance(args, Namespace)
    outputters = {'C': outputC, 'Python': outputPython}
    filenameExt = {'C': 'h', 'Python': 'py'}
    if args.verbose:
        print("Processing {}...".format(language))
    filenameBase = basename(args.specification)
    if '.' in filenameBase:
        filenameBase = filenameBase[:filenameBase.rfind('.')]
    try:
        outFile = open("{}.{}".format(filenameBase, filenameExt[language]),
                       'w')
        outputters[language](specification, outFile)
        outFile.close()
    except EnvironmentError as envErr:
        giveUp("Output environment error", envErr)
    if args.verbose:
        print("Finished processing {}.".format(language))


# Execute the following when run from the command line.
if __name__ == "__main__":
    args = parseArguments()
    if not args.test:
        specification, schema = loadAndValidateInputs(args)
        for language in args.languages:
            outputForLanguage(specification, language, args)
    else:
        import doctest
        doctest.testmod(verbose=args.verbose)

