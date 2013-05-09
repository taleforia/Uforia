'''
Created on 7 mei 2013

@author: Jimmy
'''

# This is the module for .RAR extension

# TABLE: file_names:LONGTEXT, total_files:INT, needs_password:LONGTEXT, comment:LONGTEXT, contentInfo:LONGTEXT

import sys
import traceback
import tempfile
import shutil
import rarfilelib.rarfile as rarfile
import recursive


def process(fullpath, config, rcontext, columns=None):
    # Try to parse RAR data
    try:
        # Set to full path of unrar.exe if it is not in PATH
        rarfile.UNRAR_TOOL = config.UNRAR_TOOL

        # Set up to 1 if you don't want to deal with decoding comments
        # from unknown encoding.  rarfile will try couple of common
        # encodings in sequence.
        rarfile.UNICODE_COMMENTS = 1

        rar = rarfile.RarFile(fullpath)

        assorted = [rar.namelist(), len(rar.namelist()),
                    rar.needs_password(), rar.comment]

        # Get .rar's content metadata and store it in an dictionary.
        # In the dictionary the key is the file name and
        # the value is an other dict with its info.
        content_info = {}
        for info in rar.infolist():
            content = {}
            content["date_time"] = info.date_time
            content["compress_size"] = info.compress_size
            content["CRC"] = info.CRC
            content["comment"] = info.comment
            content["volume"] = info.volume
            content["compress_type"] = info.compress_type
            content["extract_version"] = info.extract_version
            content["host_os"] = info.host_os
            content["mode"] = info.mode
            content["archival_time"] = info.arctime
            content["is_directory"] = info.isdir()
            content["needs_password"] = info.needs_password()

            content_info[info.filename] = content

        # Store content info in DB.
        assorted.append(content_info)
        del content_info

        # Try to extract the content of the rar file.
        try:
            # Create a temporary directory
            tmpdir = tempfile.mkdtemp("_uforiatmp", dir=config.EXTRACTDIR)

            # Extract the rar file
            rar.extractall(tmpdir)

            recursive.call_uforia_recursive(config, rcontext, tmpdir, fullpath)

            # Close the rar file
            rar.close()
        except:
            traceback.print_exc(file=sys.stderr)

        # Delete the temporary directory, proceed even if it causes
        # an error
        try:
            pass
            shutil.rmtree(tmpdir)
        except:
            traceback.print_exc(file=sys.stderr)

        # Make sure we stored exactly the same amount of columns as
        # specified!!
        assert len(assorted) == len(columns)

        # Print some data that is stored in the database if debug is true
        if config.DEBUG:
            print "\nRAR file data:"
            for i in range(0, len(assorted)):
                print "%-18s %s" % (columns[i] + ':', assorted[i])

        return assorted

    except:
        traceback.print_exc(file=sys.stderr)

        # Store values in database so not the whole application crashes
        return None
