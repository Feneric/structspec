#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for the Python language

Provides everything needed to output files that support the
binary format in the Python programming language.
"""

from math import pow
from os.path import basename
from zope.interface import moduleProvides
from common import writeOut, writeOutBlock, giveUp, getJsonPointer, \
    isStringType, isFloatType, isBooleanType, schemaVal, typeSizes
from interfaces import ILanguage

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

def handleBitFields(bitFieldLen, bitFieldCount, formatList, varList):
    """
    Transiently stores bitfield information.

    Determines the type of struct item for the bitfield and readies both
    the portion of the struct string and the portion of the variable
    name string for final display.

    Args:
        bitFieldLen (int):    The length of the current bitfield.
        bitFieldCount (int):  The current tally of bitfields.
        formatList (list): List of struct items to turn into string.
        varList (list):       List of variable names to turn into string.

    Returns:
        The number of bitfields processed so far.
    """
    assert isinstance(bitFieldLen, int)
    assert isinstance(bitFieldCount, int)
    assert isinstance(formatList, list)
    assert isinstance(varList, list)
    if bitFieldLen:
        if bitFieldLen <= 8:
            formatList.append('B')
        elif bitFieldLen <= 16:
            formatList.append('H')
        elif bitFieldLen <= 32:
            formatList.append('L')
        elif bitFieldLen <= 64:
            formatList.append('Q')
        else:
            print("Bitfield too long.")
        bitFieldLen = 0
        varList.append("bitField{}".format(bitFieldCount))
        bitFieldCount += 1
    return bitFieldCount


def handleStructBreaks(pyFile, formatList, countList, varList,
                       formatStrList, endianness='', prefix=''):
    """
    Writes pending lines prior to a topic shift.

    A given binary packet structure may have multiple components.
    It needs to be possible to write out everything required for
    the pieces already in place before switching to something else.

    Args:
        pyFile (file):           The file-like object to which to
                                 write data.
        formatList (list):       Struct format string elements to
                                 process.
        countList (list):        Quantity elements to process.
        varList(list):           Variable name list elements to
                                 process.
        formatStrList (list):    List of all formatLists already
                                 created.
        endianness (str):        The endianness.
        prefix (str):            A string to prepend to output lines.
    """
    assert hasattr(pyFile, 'write')
    assert isinstance(formatList, list)
    assert isinstance(countList, list)
    assert isinstance(varList, list)
    assert isinstance(formatStrList, list)
    assert isinstance(endianness, str)
    assert isinstance(prefix, str)
    if formatList:
        formatStr = ''.join(formatList)
        if countList:
            countStr = '.format({})'.format(', '.join(countList))
        else:
            countStr = ''
        formatStr = "{}{}".format(endianFormatChar.get(endianness, ''),
                                  formatStr)
        writeOut(pyFile, 'segmentFmt = "{}"{}'.format(
                 formatStr, countStr), prefix)
        writeOut(pyFile, 'segmentLen = calcsize(segmentFmt)',
                 prefix)
        writeOut(pyFile, 'position += segmentLen', prefix)
        varStr = ', '.join(varList)
        if len(varList) > 1:
            varStr = '({})'.format(varStr)
        else:
            varStr = '[{}]'.format(varStr)
        writeOut(pyFile,
                 '{} = unpack_from(segmentFmt, rawData, position)'.format(
                     varStr), prefix)
        formatStrList.append("calcsize('{}'{})".format(formatStr,
                             countStr))
        # Empty work lists
        formatList = []
        varList = []
        countList = []


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
    writeOut(pyFile, 'from struct import unpack_from, calcsize')
    writeOut(pyFile, '')

    # Parse the enumerations
    for enumerationName, enumeration in specification['enums'].items():
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
        writeOut(pyFile, '')
        writeOut(pyFile, '')

    # Parse the structure
    for packetName, packet in specification['packets'].items():
        writeOut(pyFile, 'def unpack_{}(rawData):'.format(packetName))
        prefix = '    '
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
        writeOut(pyFile, '"""', prefix)
        writeOut(pyFile, 'packet = {}', prefix)
        writeOut(pyFile, 'position = 0', prefix)
        formatList = []
        formatStrList = []
        substructureList = []
        varList = []
        countList = []
        bitFieldCount = bitFieldLen = 0
        bitFields = []
        for structureName, structure in packet['structure'].items():
            endianness = structure.get('endianness', packet.get('endianness',
                                       specification.get('endianness', None)))
            if 'description' in structure:
                writeOut(pyFile, '')
                writeOutBlock(pyFile, structure['description'], '    # ')
            line = []
            if structure['type'].startswith('#/'):
                handleStructBreaks(pyFile, formatList, countList, varList,
                                   formatStrList, endianness, prefix)
                typeName = structure['type'][structure['type'].rfind('/') + 1:]
                substructureList.append(typeName)
                line.append("packet['{}'] = unpack_{}(rawData[:position])".format(
                    structureName, typeName))
                line.append("position += get_{}_len()".format(structureName))
            else:
                typeName = structure['type']
                if 'count' in structure:
                    if structure['count'].startswith('#/'):
                        countLabel = structure['count'][:-len(schemaVal)]
                        countLabel = countLabel[countLabel.rfind('/') + 1:]
                        formatList.append('{}')
                        countList.append(countLabel)
                    else:
                        countLabel = structure['count']
                        formatList.append(countLabel)
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
                                                    formatList, varList)
                    formatList.append(typeFormatChar[typeName])
                    varList.append("packet['{}']".format(structureName))
                elif gotBitField:
                    bitFieldLen += sizeInBits
                    bitFields.append(("packet['{}']".format(structureName),
                                     bitFieldCount, sizeInBits))
            if 'title' in structure:
                line.append(' # {}'.format(structure['title']))
            if line:
                writeOut(pyFile, ''.join(line), prefix)
        bitFieldCount = handleBitFields(bitFieldLen, bitFieldCount,
                                        formatList, varList)
        handleStructBreaks(pyFile, formatList, countList, varList,
                           formatStrList, endianness, prefix)
        for bitFieldName, bitFieldNum, bitFieldSize in bitFields:
            bitFieldMask = hex(int(pow(2, bitFieldSize)))
            if isFloatType(typeName):
                bitFieldType = 'float'
            elif isBooleanType(typeName):
                bitFieldType = 'bool'
            elif isStringType(typeName):
                bitFieldType = 'str'
            else:
                bitFieldType = 'int'
            writeOut(pyFile, "{} = {}(bitField{} & {})".format(bitFieldName,
                     bitFieldType, bitFieldNum, bitFieldMask), prefix)
            writeOut(pyFile, "bitField{} <<= {}".format(bitFieldNum,
                     bitFieldSize), prefix)
        writeOut(pyFile, 'return packet', prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, '')
        # create the get length function
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
        writeOut(pyFile, '"""', prefix)
        if not formatStrList:
            formatStrList = ['0']
        writeOut(pyFile, 'totalSize = {}'.format(' + '.join(formatStrList)), prefix)
        for substruct in substructureList:
            writeOut(pyFile, 'totalSize += get_{}_len()'.format(substruct), prefix)
        writeOut(pyFile, 'return totalSize', prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, '')
        # create the validate function
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
        writeOut(pyFile, 'packet = get_{}(rawData)'.format(packetName), prefix)
        writeOut(pyFile, 'return packet', prefix)
        writeOut(pyFile, '')
        writeOut(pyFile, '')

    writeOut(pyFile, 'if __name__ == "__main__":')
    writeOut(pyFile, '    pass')


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

