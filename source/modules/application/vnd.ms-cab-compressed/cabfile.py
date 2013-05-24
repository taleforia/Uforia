# Copyright (C) 2013 Hogeschool van Amsterdam

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Module for extracting .cab files 

# TABLE: Signature:LONGTEXT, Offset:INT, Version:LONGTEXT, Folder:INT, Files:INT, OffsetFirstFile:INT, Compression:INT, Checksum:INT, SizeCompBytes:INT, SizeUnCompBytes:INT, PositionFirst:INT, WinCEHeader:INT, TargetArch:INT, MinWinCEVersion:INT, MaxWinCeVersion:INT, MinBuildNo:INT

import sys
import traceback
import tempfile
import shutil
import os
import recursive
from struct import *
from compiler.ast import For


def _uncompressed_filename(fullpath):
    lastpart = os.path.relpath(fullpath, os.path.dirname(fullpath))
    return lastpart + "~unzipped"


def process(fullpath, config, rcontext, columns=None):
    try:
         # Create a temporary directory
        tmpdir = tempfile.mkdtemp("_uforiatmp", dir=config.EXTRACTDIR)

        # Open cab file for reading
        file = open(fullpath, 'rb')
        assorted = [file.read(4)]
#        print "CAB Signature: %s\n" % file.read(4)
        cabhdr = unpack('iiiiibbhhhhh',file.read(32))
         
#        print "Offset of CFFILE entry: %d\n" % cabhdr[3]
#        print "CAB Version: %d.%d\n" % (cabhdr[6],cabhdr[5])
#        print "Total folders: %d\n" % cabhdr[7]
#        print "Total files: %d\n" % cabhdr[8]

        assorted.append(cabhdr[3])
        version = "%d.%d" % (cabhdr[6], cabhdr[5])
        assorted.append(version)
        assorted.append(cabhdr[7])
        assorted.append(cabhdr[8])

        if cabhdr[9] > 3:
            print "CAB9 > 3"
            resv = unpack('hbb',file.read(4))
        
        cabflr = unpack('ihh',file.read(8))
#        print "Offset of first file: %d\n" % cabflr[0]
#        print "Compression used: %d\n" % cabflr[2]
        assorted.append(cabflr[0])
        assorted.append(cabflr[2])
        if cabflr[2] >= 0:
            print "Unable to work with this type of compression, exiting.\n\n"
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
            assorted.append(None)
        else:
            file.seek(cabflr[0])
            cfdata = unpack('ibh',file.read(8))
#            print "Checksum: %d\n" % cfdata[0]
#            print "Size of compressed bytes: %d\n" % cfdata[1]
#            print "Size of uncompressed bytes: %d\n" % cfdata[2]
#            print "Exact position of first file: %d\n" % file.tell()
            assorted.append(cfdata[0])
            assorted.append(cfdata[1])
            assorted.append(cfdata[2])
            assorted.append(file.tell())
            
            assorted.append(file.read(4))
            
#            print "WinCE CAB Header: %s\n" % file.read(4)
            cehdr = unpack('iiiiiiiiiii',file.read(44))
#            print "Target Arch: %d\n" % cehdr[4]
#            print "Minimum Windows CE Version: %d.%d\n" % (cehdr[5],cehdr[6])
#            print "Maximum Windows CE Version: %d.%d\n" % (cehdr[7],cehdr[8])
#            print "Minimum Build number: %d.%d\n" % (cehdr[9],cehdr[10])
            
            assorted.append(cehdr[4])
            minimum_ce_version = "%d.%d" % (cehdr[5],cehdr[6])
            maximum_ce_version = "%d.%d" % (cehdr[7],cehdr[8])
            minimum_build_number = "%d.%d" % (cehdr[9],cehdr[10])
            assorted.append(minimum_ce_version)
            assorted.append(maximum_ce_version)
            assorted.append(minimum_build_number)
 
        assert len(assorted) == len(columns)
        return assorted
    except:
        traceback.print_exc(file=sys.stderr)
    return None