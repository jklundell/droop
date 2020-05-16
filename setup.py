#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
build droop release package

Copyright 2010 by Jonathan Lundell

This file is part of Droop.

    Droop is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Droop is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Droop.  If not, see <http://www.gnu.org/licenses/>.
'''

from setuptools import setup, find_packages
from droop import common

setup(name = common.droopName,
    version = common.droopVersion,
    author = common.droopAuthor,
    author_email = common.droopAuthorEmail,
    url = common.droopURL,
    license = common.droopLicense,
    description = common.droopDescription,
    long_description = common.droopLongDescription,
    script_args = ['bdist_wheel'],
    python_requires='>=3.6',
    py_modules=["Droop", 'irv', 'mpls', 'oscar', 'scotland'],
    packages = find_packages(),
    include_package_data = True,
    package_data = {
        'test': ['*.sh',
        'blt/*.blt', 'blt/*/*.blt',
        'ref/*/*.txt', 'ref/*/*/*.txt',
        ],
        'droop': ['COPYING']
    },
    )
