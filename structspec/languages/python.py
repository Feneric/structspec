#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for the Python language

Provides everything needed to output files that support the
binary format in the Python programming language.
"""

from math import pow
from os.path import basename
from os import linesep
from re import compile as regexpcompile
from struct import calcsize
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from zope.interface import moduleProvides
from structspec.common import writeOut, writeOutBlock, giveUp, getJsonPointer, \
    isStringType, isFloatType, isBooleanType, schemaVal, typeSizes
from structspec.interfaces import ILanguage

moduleProvides(ILanguage)

name = "Python"
filenameExtension = 'py'

# Get a workable JSON pointer resolver from whichever library
resolveJsonPointer = getJsonPointer()


# The Python struct library characters for data types
typeFormatChar = {
    "char": 'c',
    "signed char": 'b',
    "unsigned char": 'B',
    "short": 'h',
    "signed short": 'h',
    "unsigned short": 'H',
    "short int": 'h',
    "signed short int": 'h',
    "unsigned short int": 'H',
    "int": 'i',
    "signed int": 'i',
    "unsigned int": 'I',
    "long": 'l',
    "signed long": 'l',
    "unsigned long": 'L',
    "long int": 'l',
    "signed long int": 'l',
    "unsigned long int": 'L',
    "long long": 'q',
    "signed long long": 'q',
    "unsigned long long": 'Q',
    "long long int": 'q',
    "signed long long int": 'q',
    "unsigned long long int": 'Q',
    "float": 'f',
    "double": 'd',
    "long double": 'QQ',
    "bool": 'i',
    "boolean": '?',
    "_Bool": '?',
    "int8_t": 'b',
    "uint8_t": 'B',
    "int16_t": 'h',
    "uint16_t": 'H',
    "int24_t": 'BH',
    "uint24_t": 'BH',
    "int32_t": 'l',
    "uint32_t": 'L',
    "int64_t": 'q',
    "uint64_t": 'Q',
    "hollerith": 'c',
    "string": 's',
    "str": 's',
    "pascal": 'p',
    "pointer": 'P',
    "void": 'P',
    "padding": 'x'
}

# The Python struct library characters for endianness
endianFormatChar = {
    "big": '>',
    "little": '<',
    "network": '!',
    "native": '@'
}

# compiled regular expressions
varNameRE = regexpcompile(r'^[A-Z_a-z]\w*$')
exprPortion = r'[\w\s+*/%()\[\]-]+'
exprRE = regexpcompile(r'^{}$'.format(exprPortion))
structFmtRE = regexpcompile(r'^"([>{{}}!=<@]*[cbBhHiIlLqQfd?spPx]+)"(\.format\({}\))*$'.format(exprPortion))


def outputEnumerations(enumerationSpec, options, pyFile):
    """
    Outputs the enmerations into a Python file.

    Given the portion of the specification definining all
    the enumerations, output options and an output file,
    write out all the necessary enumerations definitions
    and return information on their values for use in
    future parsing.

    Args:
        enumerationSpec (dict): The portion of the
                                specification covering
                                enumerations.
        options (dict):         A dictionary of options to
                                modify output.
        pyFile (file):          A file-like object to which
                                to save the struct code.

    Returns:
        A dictionary of constants to be pulled into the
        environment for parsing structure definitions.
    """
    assert isinstance(enumerationSpec, list)
    assert isinstance(options, dict)
    assert hasattr(pyFile, 'write')
    newLocals = []
    for enumerationName, enumeration in enumerationSpec:
        writeOut(pyFile, '##')
        if 'title' in enumeration:
            writeOut(pyFile, enumeration['title'], '# ')
        else:
            writeOut(pyFile, enumerationName, '# ')
        if 'description' in enumeration:
            writeOut(pyFile, '#')
            writeOutBlock(pyFile, enumeration['description'], '# ')
        writeOut(pyFile, '#')
        varType = enumeration.get('type', None)
        value = None
        for optionName, option in enumeration['options'].items():
            line = []
            if 'description' in option:
                writeOut(pyFile, '    #')
                writeOutBlock(pyFile, option['description'], '    # ')
                writeOut(pyFile, '    #')
            if 'value' in option:
                varType = option.get('type', varType)
                if isStringType(varType):
                    varType = 'str'
                elif isFloatType(varType):
                    varType = 'float'
                elif isBooleanType(varType):
                    varType = 'bool'
                else:
                    varType = 'int'
                if varType is None:
                    if options['verbose']:
                        print('Guessing enumeration type based on value.')
                    varType = str(type(option['value']))[7:-2]
                    if varType == 'str' and (value.startswith('(') and
                                             value.endswith(')')):
                        varType = 'int'
                        if options['verbose']:
                            print('Second-guessing enumeration type.')
                value = option['value']
            else:
                if varType is None:
                    varType = 'int'
                    if options['verbose']:
                        print('Defaulting enumeration type to int.')
                if not isinstance(value, int):
                    value = 0
                else:
                    value += 1
            if varType == str:
                delim = '"'
            else:
                delim = ''
            line.append(optionName)
            line.append(' = {}{}{}'.format(delim, value, delim))
            if 'title' in option:
                line.append(' # {}'.format(option['title']))
            writeOut(pyFile, ''.join(line))
            newLocals.append((optionName, value))
        writeOut(pyFile, '')
        writeOut(pyFile, '')
    return newLocals


def handleBitFields(bitFieldLen, bitFieldCount, structAccretions):
    """
    Transiently stores bitfield information.

    Determines the type of struct item for the bitfield and readies both
    the portion of the struct string and the portion of the variable
    name string for final display.

    Args:
        bitFieldLen (int):       The length of the current bitfield.
        bitFieldCount (int):     The current tally of bitfields.
        structAccretions (dict): Structure information collected
                                 since last processing time.

    Returns:
        The number of bitfields processed so far.

    Examples:
        >>> accretions = {'formatList': [], 'varList': []}
        >>> handleBitFields(5, 0, accretions)
        1
        >>> accretions['formatList']
        ['B']
        >>> accretions['varList']
        ['bitField0']
        >>> handleBitFields(15, 1, accretions)
        2
        >>> accretions['formatList']
        ['B', 'H']
        >>> accretions['varList']
        ['bitField0', 'bitField1']
    """
    assert isinstance(bitFieldLen, int)
    assert isinstance(bitFieldCount, int)
    assert isinstance(structAccretions, dict)
    assert isinstance(structAccretions['formatList'], list) and \
        isinstance(structAccretions['varList'], list)
    if bitFieldLen:
        if bitFieldLen <= 8:
            structAccretions['formatList'].append('B')
        elif bitFieldLen <= 16:
            structAccretions['formatList'].append('H')
        elif bitFieldLen <= 32:
            structAccretions['formatList'].append('L')
        elif bitFieldLen <= 64:
            structAccretions['formatList'].append('Q')
        else:
            print("Bitfield too long.")
        bitFieldLen = 0
        structAccretions['varList'].append(
            "bitField{}".format(bitFieldCount))
        bitFieldCount += 1
    return bitFieldCount


def handleStructBreaks(structDefList, structAccretions, endianness=''):
    """
    Writes pending lines prior to a topic shift.

    A given binary packet structure may have multiple components.
    It needs to be possible to write out everything required for
    the pieces already in place before switching to something else.

    Args:
        structDefList (list):    List of items in the structure.
        structAccretions (dict): Structure information collected
                                 since last processing time.
        endianness (str):        The endianness.
    """
    assert isinstance(structDefList, list)
    assert isinstance(structAccretions, dict)
    assert isinstance(structAccretions['formatList'], list) and \
        isinstance(structAccretions['countList'], list) and \
        isinstance(structAccretions['varList'], list) and \
        isinstance(structAccretions['bitFields'], list)
    assert isinstance(endianness, str)
    if structAccretions['formatList']:
        formatStr = ''.join(structAccretions['formatList'])
        if structAccretions['countList']:
            countStr = '.format({})'.format(
                ', '.join(structAccretions['countList']))
        else:
            countStr = ''
        formatStr = "{}{}".format(endianFormatChar.get(endianness, ''),
                                  formatStr)
        varStr = ', '.join(structAccretions['varList'])
        if len(structAccretions['varList']) > 1:
            varStr = '({})'.format(varStr)
        else:
            varStr = '[{}]'.format(varStr)
        structDefList.append({
            'type': 'segment',
            'fmt': '"{}"{}'.format(formatStr, countStr),
            'vars': varStr,
            'bitFields': structAccretions['bitFields'],
            'endianness': endianness,
            'titles': structAccretions['titles'],
            'description': structAccretions['descriptions']
        })
        # Empty work lists
        structAccretions['formatList'] = []
        structAccretions['varList'] = []
        structAccretions['countList'] = []
        structAccretions['bitFields'] = []
        structAccretions['titles'] = []
        structAccretions['descriptions'] = []


def populateWorkLists(packet, specification,
                      structDefList, structAccretions):
    """
    Loads work lists based on packet portion of spec.

    Given the portion of the specification definining a
    packets, the specification itself, and the work lists,
    populate them with the relevant information gleaned
    from the packet definition.

    Args:
        packet (dict):           The definition of the
                                 individual packet being
                                 processed.
        specification (dict):    The specification object.
        structDefList (list):    List of items in the
                                 structure.
        structAccretions (dict): Structure information collected
                                 since last processing time.

    Returns:
        A tuple containing the bitfield count and bitfield
        length.
    """
    assert isinstance(packet, dict)
    assert isinstance(specification, dict)
    assert isinstance(structDefList, list)
    assert isinstance(structAccretions, dict)
    assert isinstance(structAccretions['formatList'], list) and \
        isinstance(structAccretions['countList'], list) and \
        isinstance(structAccretions['varList'], list) and \
        isinstance(structAccretions['bitFields'], list)
    bitFieldCount = bitFieldLen = 0
    for structureName, structure in packet['structure'].items():
        endianness = structure.get('endianness', packet.get('endianness',
                                   specification.get('endianness', ''))).encode('utf-8')
        if structure['type'].startswith('#/'):
            handleStructBreaks(structDefList, structAccretions, endianness)
            typeName = structure['type'][structure['type'].rfind('/') + 1:]
            structDefList.append({
                'type': 'substructure',
                'itemName': structureName,
                'itemType': typeName,
                'description': structure.get('description', None),
                'title': structure.get('title', None)
            })
        else:
            typeName = structure['type']
            if 'count' in structure:
                if structure['count'].startswith('#/'):
                    countLabel = structure['count'][:-len(schemaVal)]
                    countLabel = countLabel[countLabel.rfind('/') + 1:]
                    structAccretions['formatList'].append('{}')
                    structAccretions['countList'].append(countLabel)
                else:
                    countLabel = structure['count']
                    structAccretions['formatList'].append(countLabel)
            gotBitField = False
            if 'size' in structure:
                if structure['size'].startswith('#/'):
                    sizeLabel = structure['size'][:-len(schemaVal)]
                    sizeLabel = sizeLabel[sizeLabel.rfind('/') + 1:]
                    sizeInBits = resolveJsonPointer(specification,
                                                    structure['size'][1:])
                else:
                    sizeLabel = structure['size']
                    try:
                        sizeInBits = int(sizeLabel)
                    except ValueError:
                        sizeInBits = 0
                if sizeInBits != typeSizes.get(typeName, -1) or \
                   sizeInBits % 8 != 0:
                    gotBitField = True
            if typeName in typeFormatChar and not gotBitField:
                bitFieldCount = handleBitFields(bitFieldLen, bitFieldCount,
                                                structAccretions)
                bitFieldLen = 0
                structAccretions['formatList'].append(typeFormatChar[typeName])
                structAccretions['varList'].append(
                    "packet['{}']".format(structureName))
                structAccretions['titles'].append(structure.get('title', None))
                structAccretions['descriptions'].append(structure.get('title', None))
            elif gotBitField:
                bitFieldLen += sizeInBits
                structAccretions['bitFields'].append(
                    ("packet['{}']".format(structureName),
                     bitFieldCount, sizeInBits, typeName))
    bitFieldCount = handleBitFields(bitFieldLen, bitFieldCount,
                                    structAccretions)
    handleStructBreaks(structDefList, structAccretions, endianness)
    return bitFieldCount


def outputPython(specification, options, pyFile):
    """
    Outputs Python struct file.

    Given the specification construct a valid Python struct
    file that describes all the binary packets.

    Args:
        specification (dict): The specification object.
        options (dict):       A dictionary of options to
                              modify output.
        pyFile (file):        A file-like object to which
                              to save the struct code.
    """
    assert isinstance(specification, dict)
    assert isinstance(options, dict)
    assert hasattr(pyFile, 'write')
    packetLengths = {}
    writeOut(pyFile, '#!/usr/bin/env python')
    writeOut(pyFile, '# -*- coding: utf-8 -*-')
    writeOut(pyFile, '"""')
    writeOut(pyFile, specification['title'])
    if 'description' in specification:
        writeOut(pyFile, '')
        writeOutBlock(pyFile, specification['description'])
    for tag in ('version', 'date', 'author', 'documentation', 'metadata'):
        if tag in specification:
            writeOut(pyFile, '')
            writeOut(pyFile, '{}: {}'.format(tag.title(),
                                             specification[tag]))
    writeOut(pyFile, '"""')
    writeOut(pyFile, '')
    writeOut(pyFile, 'from struct import calcsize, pack, unpack_from')
    writeOut(pyFile, 'from zope.interface import directlyProvides, Interface')
    writeOut(pyFile, '')
    writeOut(pyFile, '')
    prefix = '    '

    # Create interfaces for testing and documenting
    extensionlessName = options['pyFilename'].split('.')[0]
    extensionlessName = extensionlessName[0].upper() + extensionlessName[1:]
    writeOut(pyFile, 'class I{}Length(Interface):'.format(extensionlessName))
    writeOut(pyFile, '"""', prefix)
    writeOut(pyFile, 'A binary packet length calculator', prefix)
    writeOut(pyFile, '')
    writeOut(pyFile, 'Interface for an entity that returns the length ' \
             + 'of a binary packet buffer.', prefix)
    writeOut(pyFile, '"""', prefix)
    writeOut(pyFile, 'def __call__():', prefix)
    writeOut(pyFile, '"""Returns the length of the object in bytes."""',
             2 * prefix)
    writeOut(pyFile, '')
    writeOut(pyFile, '')
    writeOut(pyFile, 'class I{}Packer(Interface):'.format(extensionlessName))
    writeOut(pyFile, '"""', prefix)
    writeOut(pyFile, 'A binary data packer', prefix)
    writeOut(pyFile, '')
    writeOut(pyFile, 'Interface for an entity that packs binary data.', prefix)
    writeOut(pyFile, '"""', prefix)
    writeOut(pyFile, 'def __call__(packet):', prefix)
    writeOut(pyFile, '"""Packs a packet dict into a string."""', 2 * prefix)
    writeOut(pyFile, '')
    writeOut(pyFile, '')
    writeOut(pyFile, 'class I{}Unpacker(Interface):'.format(extensionlessName))
    writeOut(pyFile, '"""', prefix)
    writeOut(pyFile, 'A binary data unpacker', prefix)
    writeOut(pyFile, '')
    writeOut(pyFile, 'Interface for an entity that unpacks binary data.',
             prefix)
    writeOut(pyFile, '"""', prefix)
    writeOut(pyFile, 'def __call__(buffer):', prefix)
    writeOut(pyFile, '"""Unpacks a binary string into a dict."""', 2 * prefix)
    writeOut(pyFile, '')
    writeOut(pyFile, '')


    # Parse the enumerations
    newLocals = outputEnumerations(specification['enums'].items(),
                                   options, pyFile)
    # The following is a little ugly but places the enumerations
    # in the current namespace so that they may be referenced
    # when evaluating formats.
    for optionName, value in newLocals:
        if varNameRE.match(optionName) and exprRE.match(str(value)):
            exec '{} = {}'.format(optionName, value)

    # Parse the structure
    for packetName, packet in specification['packets'].items():
        structDefList = []
        structAccretions = {
            'formatList': [],
            'countList': [],
            'varList': [],
            'bitFields': [],
            'titles': [],
            'descriptions': []
        }
        bitFieldCount = populateWorkLists(
            packet, specification,
            structDefList, structAccretions
        )

        # Create the get length function
        writeOut(pyFile, 'def get_{}_len():'.format(packetName))
        writeOut(pyFile, '"""', prefix)
        writeOut(pyFile, "Calculates the size of {}.".format(packetName), prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, "Calculates the total size of the {} structure".format(
                 packetName), prefix)
        writeOut(pyFile, "(including any internal substructures).", prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Returns:', prefix)
        writeOut(pyFile, 'The size of {}.'.format(packetName),
                 2 * prefix)
        # The following section determines how many bytes a packet
        # consists of so we can make good doctests. To do so it
        # evaluates the expressions used for the format descriptions.
        packetLen = 0
        try:
            for structDef in structDefList:
                if structDef['type'] == 'segment':
                    assert structFmtRE.match(structDef['fmt'])
                    packetLen += calcsize(eval(structDef['fmt']))
                elif structDef['type'] == 'substructure':
                    packetLen += packetLengths[structDef['itemType']]
            packetLengths[packetName] = packetLen
            writeOut(pyFile, '')
            writeOut(pyFile, 'Examples:', prefix)
            writeOut(pyFile, '>>> get_{}_len()'.format(packetName), prefix * 2)
            writeOut(pyFile, '{}'.format(packetLen), prefix * 2)
        except KeyError:
            # If we can't evaluate it don't bother with a doctest
            # for this one. This can happen if dependencies get
            # defined after they're used.
            pass
        writeOut(pyFile, '"""', prefix)
        # Create the function itself.
        formatStrList = [structDef['fmt'] for structDef in structDefList
                         if structDef['type'] == 'segment']
        if not formatStrList:
            writeOut(pyFile, 'totalSize = 0', prefix)
        else:
            writeOut(pyFile, 'totalSize = calcsize({})'.format(
                     ') + calcsize('.join(formatStrList)), prefix)
        substructureList = [structDef['itemType'] for structDef in structDefList
                            if structDef['type'] == 'substructure']
        for substruct in substructureList:
            writeOut(pyFile, 'totalSize += get_{}_len()'.format(substruct), prefix)
        writeOut(pyFile, 'return totalSize', prefix)
        writeOut(pyFile, 'directlyProvides(get_{}_len, I{}Length)'.format(
                 packetName, extensionlessName))
        writeOut(pyFile, '')
        writeOut(pyFile, '')

        # Create the pack function
        writeOut(pyFile, 'def pack_{}(packet):'.format(packetName))
        writeOut(pyFile, '"""', prefix)
        writeOut(pyFile, "Packs a {} packet.".format(packetName), prefix)
        if 'description' in packet:
            writeOut(pyFile, '')
            writeOutBlock(pyFile, packet['description'], prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Args:', prefix)
        writeOut(pyFile, 'packet (dict): A dictionary of data to be packed.',
                 2 * prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Returns:', prefix)
        writeOut(pyFile, 'A binary string containing the packed data.',
                 2 * prefix)
        writeOut(pyFile, '"""', prefix)
        writeOut(pyFile, 'assert isinstance(packet, dict)', prefix)
        writeOut(pyFile, 'outList = []', prefix)
        for structDef in structDefList:
            if structDef['type'] == 'segment':
                for fragNum, (bitFieldName, bitFieldNum, bitFieldSize, bitFieldLabel
                              ) in enumerate(reversed(structDef['bitFields'])):
                    if fragNum == 0:
                        writeOut(pyFile, 'bitField{} = {}'.format(
                            bitFieldNum, bitFieldName), prefix)
                    else:
                        writeOut(pyFile, 'bitField{} <<= {}'.format(
                            bitFieldNum, bitFieldSize), prefix)
                        writeOut(pyFile, 'bitField{} |= {}'.format(
                            bitFieldNum, bitFieldName), prefix)
                writeOut(pyFile, 'outList.append(pack({}, {}))'.format(
                    structDef['fmt'], structDef['vars'][1:-1]), prefix)
            elif structDef['type'] == 'substructure':
                writeOut(pyFile, 'outList.append(pack_{}(packet["{}"]))'.format(
                    structDef['itemType'], structDef['itemName']), prefix)
        writeOut(pyFile, 'return "".join(outList)', prefix)
        writeOut(pyFile, 'directlyProvides(pack_{}, I{}Packer)'.format(
                 packetName, extensionlessName))
        writeOut(pyFile, '')
        writeOut(pyFile, '')

        # Create the unpack function
        writeOut(pyFile, 'def unpack_{}(rawData):'.format(packetName))
        writeOut(pyFile, '"""', prefix)
        if 'title' in packet:
            writeOut(pyFile, packet['title'], prefix)
        else:
            writeOut(pyFile, packetName, prefix)
        if 'description' in packet:
            writeOut(pyFile, '')
            writeOutBlock(pyFile, packet['description'], prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Args:', prefix)
        writeOut(pyFile, 'rawData (str): The raw binary data to be unpacked.',
                 2 * prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Returns:', prefix)
        writeOut(pyFile, 'A dictionary of the unpacked data.',
                 2 * prefix)
        # Write out the next bit to a temporary buffer.
        outBufStr = StringIO()
        writeOut(outBufStr, '"""', prefix)
        writeOut(outBufStr, 'assert isinstance(rawData, str)', prefix)
        writeOut(outBufStr, 'packet = {}', prefix)
        writeOut(outBufStr, 'position = 0', prefix)
        for structDef in structDefList:
            line = []
            if structDef['type'] == 'segment':
                line.append('segmentFmt = {}{}'.format(structDef['fmt'], linesep))
                line.append('{}segmentLen = calcsize(segmentFmt){}'.format(prefix, linesep))
                line.append('{}{} = unpack_from(segmentFmt, rawData, position){}'.format(
                            prefix, structDef['vars'], linesep))
                line.append('{}position += segmentLen{}'.format(prefix, linesep))
                for fragNum, (bitFieldName, bitFieldNum, bitFieldSize,
                              bitFieldLabel) in enumerate(structDef['bitFields']):
                    bitFieldMask = hex(int(pow(2, bitFieldSize)) - 1)
                    if isFloatType(bitFieldLabel):
                        bitFieldType = 'float'
                    elif isBooleanType(bitFieldLabel):
                        bitFieldType = 'bool'
                    elif isStringType(bitFieldLabel):
                        bitFieldType = 'str'
                    else:
                        bitFieldType = 'int'
                    line.append("{}{} = {}(bitField{} & {}){}".format(prefix, bitFieldName,
                                bitFieldType, bitFieldNum, bitFieldMask, linesep))
                    if fragNum < len(structDef['bitFields']) - 1:
                        line.append("{}bitField{} >>= {}{}".format(prefix,
                                    bitFieldNum, bitFieldSize, linesep))
                if line[-1].endswith(linesep):
                    line[-1] = line[-1][:-len(linesep)]
            elif structDef['type'] == 'substructure':
                if structDef['description']:
                    writeOut(outBufStr, '')
                    writeOutBlock(outBufStr, structDef['description'], '    # ')
                line.append("packet['{}'] = unpack_{}(rawData[position:]){}".format(
                    structDef['itemName'], structDef['itemType'], linesep))
                line.append("{}position += get_{}_len()".format(
                    prefix, structDef['itemType']))
                if structDef['title']:
                    line.append(' # {}'.format(structDef['title']))
            if line:
                writeOut(outBufStr, ''.join(line), prefix)
        writeOut(outBufStr, 'return packet', prefix)
        writeOut(outBufStr, 'directlyProvides(unpack_{}, I{}Unpacker)'.format(
                 packetName, extensionlessName))
        # Write the temporary buffer to the output file.
        writeOut(pyFile, outBufStr.getvalue())
        outBufStr.close()
        writeOut(pyFile, '')

        # Create the validate function
        writeOut(pyFile, 'def validate_{}(rawData):'.format(packetName))
        writeOut(pyFile, '"""', prefix)
        writeOut(pyFile, "Reads and validates a {} packet.".format(packetName), prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, "Reads a {} structure from raw binary data".format(
                 packetName), prefix)
        writeOut(pyFile, "and validates it.", prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Args:', prefix)
        writeOut(pyFile, 'rawData (str): The raw binary data to be unpacked.',
                 2 * prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, 'Returns:', prefix)
        writeOut(pyFile, 'A structure representing the {} packet.'.format(packetName),
                 2 * prefix)
        writeOut(pyFile, '"""', prefix)
        writeOut(pyFile, 'assert isinstance(rawData, str)', prefix)
        writeOut(pyFile, 'packet = get_{}(rawData)'.format(packetName), prefix)
        writeOut(pyFile, 'return packet', prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, '')

    writeOut(pyFile, 'if __name__ == "__main__":')
    writeOut(pyFile, 'from zope.interface.verify import verifyObject', prefix)
    writeOut(pyFile, 'import doctest', prefix)
    writeOut(pyFile, 'doctest.testmod()', prefix)


def outputForLanguage(specification, options):
    """
    Outputs handler files for given language.

    Creates files to process given specification in given
    programming language.  Bases output file names on given
    input specification file.

    Args:
        specification (dict): The specification object.
        options (dict):       Command-line options.
    """
    assert isinstance(specification, dict)
    assert isinstance(options, dict)
    if options['verbose']:
        print("Processing {}...".format(name))
    filenameBase = basename(options['specificationName'])
    if '.' in filenameBase:
        filenameBase = filenameBase[:filenameBase.rfind('.')]
    try:
        pyFilename = "{}.{}".format(filenameBase, filenameExtension)
        options['pyFilename'] = pyFilename
        pyFile = open(pyFilename, 'w')
        outputPython(specification, options, pyFile)
        pyFile.close()
    except EnvironmentError as envErr:
        giveUp("Output environment error", envErr)
    if options['verbose']:
        print("Finished processing {}.".format(name))


# Execute the following when run from the command line.
if __name__ == "__main__":
    import doctest
    doctest.testmod()
