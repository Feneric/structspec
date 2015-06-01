#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lang C: Support for the C language

Provides everything needed to output files that support the
binary format in the C programming language.
"""

from os.path import basename
from zope.interface import moduleProvides
from structspec.common import writeOut, writeOutBlock, giveUp,\
    getJsonPointer, schemaVal, typeSizes
from structspec.interfaces import ILanguage

moduleProvides(ILanguage)

name = "C"
filenameExtension = ('h', 'c')
resolveJsonPointer = getJsonPointer()


def outputC(specification, options, hFile, cFile):
    """
    Outputs C header file.

    Given the specification construct a valid C header
    file that describes all the binary packets.

    Args:
        specification (dict): The specification object.
        options (dict):       A dictionary of options to
                              modify output.
        hFile (file):         A file-like object to which
                              to save the header.
        cFile (file):         A file-like object to which
                              to save the C code.
    """
    assert isinstance(specification, dict)
    assert hasattr(hFile, 'write')
    assert hasattr(cFile, 'write')
    writeOut(cFile, '/** @file {} */'.format(options['cFilename']))
    writeOut(cFile, '#include "{}"'.format(options['hFilename']))
    defName = "STRUCTSPEC_{}_H".format(specification['id'].upper())
    writeOut(hFile, '/** @file {} */'.format(options['hFilename']))
    writeOut(hFile, '#ifndef {}'.format(defName))
    writeOut(hFile, '#define {}'.format(defName))
    writeOut(hFile, '#ifdef __cplusplus')
    writeOut(hFile, 'extern "C"')
    writeOut(hFile, '{')
    writeOut(hFile, '#endif /* __cplusplus */')
    writeOut(hFile, '')
    writeOut((hFile, cFile), '/**')
    prefix = ' * '
    writeOut((hFile, cFile), '@brief\t{}'.format(specification['title']),
             prefix)
    if 'description' in specification:
        writeOut((hFile, cFile), ' *')
        writeOutBlock((hFile, cFile), '@details\t'.format(
                      specification['description']), prefix)
    for tag in ('version', 'date', 'author'):
        if tag in specification:
            writeOut((hFile, cFile), ' *')
            writeOut((hFile, cFile), '@{}\t{}'.format(tag,
                                                      specification[tag]),
                     prefix)
    for tag in ('documentation', 'metadata'):
        if tag in specification:
            writeOut((hFile, cFile), ' *')
            writeOut((hFile, cFile), '[{}]({})'.format(tag.title(),
                                                       specification[tag]),
                     prefix)
    writeOut((hFile, cFile), ' */')
    writeOut((hFile, cFile), '')
    writeOut(hFile, '#include <stdint.h>')
    writeOut(hFile, '')
    for enumerationName, enumeration in specification['enums'].items():
        if not enumeration.get('preprocessor', False):
            writeOut(hFile, '/**')
            writeOut(hFile, '@enum\t{}'.format(enumerationName), ' * ')
        else:
            writeOut(hFile, '/*')
        if 'title' in enumeration:
            writeOut(hFile, enumeration['title'], ' * ')
        else:
            writeOut(hFile, enumerationName, ' * ')
        if 'description' in enumeration:
            writeOut(hFile, ' *')
            writeOutBlock(hFile, enumeration['description'], ' * ')
        writeOut(hFile, ' */')
        if enumeration.get('preprocessor', False):
            for optionName, option in enumeration['options'].items():
                line = []
                if 'description' in option:
                    writeOut(hFile, '/**')
                    writeOutBlock(hFile, option['description'], ' * ')
                    writeOut(hFile, ' */')
                line.append('#define ')
                line.append(optionName)
                if 'value' in option:
                    line.append(' {}'.format(option['value']))
                if 'title' in option:
                    line.append(' /** {} */'.format(option['title']))
                writeOut(hFile, ''.join(line))
        else:
            writeOut(hFile, "typedef enum {")
            lastOption = enumeration['options'].keys()[-1]
            for optionName, option in enumeration['options'].items():
                line = []
                if 'description' in option:
                    writeOut(hFile, '  /**')
                    writeOutBlock(hFile, option['description'], '   * ')
                    writeOut(hFile, '   */')
                line.append(optionName)
                if 'value' in option:
                    line.append(' = {}'.format(option['value']))
                if 'title' in option:
                    line.append(' /** {} */'.format(option['title']))
                if optionName != lastOption:
                    line.append(',')
                writeOut(hFile, ''.join(line), '  ')
            writeOut(hFile, "}} {};".format(enumerationName))
        writeOut(hFile, '')
    for packetName, packet in specification['packets'].items():
        writeOut(hFile, "typedef struct {")
        for structureName, structure in packet['structure'].items():
            line = []
            if 'description' in structure:
                writeOut(hFile, '  /**')
                writeOutBlock(hFile, structure['description'], '   * ')
                writeOut(hFile, '   */')
            if structure['type'].startswith('#/'):
                typeName = structure['type'][structure['type'].rfind('/') + 1:]
            else:
                typeName = structure['type']
            line.append(typeName)
            line.append(' ')
            line.append(structureName)
            if 'count' in structure:
                if structure['count'].startswith('#/'):
                    countLabel = structure['count'][:-len(schemaVal)]
                    countLabel = countLabel[countLabel.rfind('/') + 1:]
                else:
                    countLabel = structure['count']
                line.append('[{}]'.format(countLabel))
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
                if sizeInBits != typeSizes.get(typeName, -1):
                    line.append(' : {}'.format(sizeLabel))
            if 'title' in structure:
                line.append(' /** {} */'.format(structure['title']))
            line.append(';')
            writeOut(hFile, ''.join(line), '  ')
        writeOut(hFile, "}} {};".format(packetName))
        writeOut(hFile, '')
    writeOut(hFile, '#ifdef __cplusplus')
    writeOut(hFile, '}')
    writeOut(hFile, '#endif /* __cplusplus */')
    writeOut(hFile, '#endif /* {} */'.format(defName))


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
        hFilename = "{}.{}".format(filenameBase, filenameExtension[0])
        cFilename = "{}.{}".format(filenameBase, filenameExtension[1])
        hFile = open(hFilename, 'w')
        cFile = open(cFilename, 'w')
        options['hFilename'] = hFilename
        options['cFilename'] = cFilename
        outputC(specification, options, hFile, cFile)
        cFile.close()
        hFile.close()
    except EnvironmentError as envErr:
        giveUp("Output environment error", envErr)
    if options['verbose']:
        print("Finished processing {}.".format(name))


# Execute the following when run from the command line.
if __name__ == "__main__":
    import doctest
    doctest.testmod()
