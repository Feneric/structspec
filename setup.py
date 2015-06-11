#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from os.path import dirname, join
from os import chdir

#if dirname(__file__):
#    chdir(dirname(__file__))

setup(
    name='structspec',
    version='0.1.2',
    description='Language-independent binary packet structure specification',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    keywords='software development JSON Schema Python JavaScript C C++ Nim',
    author='Eric W. Brown',
    url='https://github.com/Feneric/structspec',
    packages=find_packages(),
    test_suite='structspec.test.test_structspec',
    install_requires = [
        'jsonschema', 'jsonpointer', 'json-spec', 'zope.interface'
    ],
    extras_require = {
        'documentation': ["doxypypy"]
    },
    entry_points={
        'console_scripts': [
            'structspec = structspec.structspec:main'
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: JavaScript',
        'Topic :: Software Development'
    ]
)

