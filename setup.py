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
import droop.common

setup(name = droop.common.droopName,
    version = droop.common.droopVersion,
    author = droop.common.droopAuthor,
    author_email = droop.common.droopAuthorEmail,
    url = droop.common.droopURL,
    license = droop.common.droopLicense,
    description = droop.common.droopDescription,
    long_description = droop.common.droopLongDescription,
    script_args = ['bdist_egg'],
    platforms = ['Python 2.7'],
    packages = find_packages(),
    )
