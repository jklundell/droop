#!/usr/bin/env python
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
setup(name = "droop", 
    version = "0.1", 
    script_args = ['bdist_egg'],
    author = "Jonathan Lundell",
    author_email = "jlundell@prfound.org",
    url = "http://prfound.org", # for now
    license = "GNU General Public License version 3",
    description = "Counting software for STV elections",
    long_description = "Droop is a flexible counting package for STV elections.",
    platforms = ["Python 2.6"],
    packages = find_packages(),
    )
