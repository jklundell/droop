#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' 
Unit test for droop.election package

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
import sys, os, re
testdir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.normpath(os.path.join(testdir, '..'))
if basedir not in sys.path: sys.path.insert(0, os.path.normpath(basedir))

from droop.election import Election
from droop.profile import ElectionProfile

pyflakes = True # dummy for pyflakes

def doDumpCompare(options, file, subdir=''):
    '''
    helper: do a count and compare dump/report to reference
    '''
    if not file.endswith('.blt'):
        file += '.blt'
    base, ext = os.path.splitext(file)
        
    blt = os.path.join(testdir, 'blt', subdir, file)
    E = Election(ElectionProfile(blt), options)
    E.count()
    tag = '%s-%s-%s' % (base, E.rule.tag(), E.V.tag())

    def readFile(path):
        "read a dump/report file"
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data
        
    def writeFile(path, data):
        "write a dump/report file"
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        f = open(path, 'w')
        f.write(data)
        f.close()
        
    #  first do dump
    #
    dref = os.path.join(testdir, 'ref', 'dump', subdir, '%s.txt' % tag)
    dout = os.path.join(testdir, 'out', 'dump', subdir, '%s.txt' % tag)
    dump = E.dump()
    if not os.path.isfile(dref):
        writeFile(dref, dump)
    dumpref = readFile(dref)
    if os.path.isfile(dout):
        os.unlink(dout)
    if dump != dumpref:
        writeFile(dout, dump)
        return False

    #  same logic with report
    #
    rref = os.path.join(testdir, 'ref', 'report', subdir, '%s.txt' % tag)
    rout = os.path.join(testdir, 'out', 'report', subdir, '%s.txt' % tag)
    report = E.report()
    if not os.path.isfile(rref):
        writeFile(rref, report)
    reportref = readFile(rref)
    if os.path.isfile(rout):
        os.unlink(rout)
    # don't include version number in comparison
    report0 = re.sub(r'droop v\d+\.\d+', 'droop v0.0', report)
    reportref = re.sub(r'droop v\d+\.\d+', 'droop v0.0', reportref)
    if report0 != reportref:
        writeFile(rout, report)
        return False
    return True

