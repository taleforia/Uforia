#!/usr/bin/env python

# Copyright (C) 2013-2015 A. Eijkhoudt and others

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# This is the module for handling rfc822 email types

# Do not change from CamelCase because these are the official header names
# TABLE: Delivered_To:LONGTEXT, Original_Recipient:LONGTEXT, Received:LONGTEXT, Return_Path:LONGTEXT, Received_SPF:LONGTEXT, Authentication_Results:LONGTEXT, DKIM_Signature:LONGTEXT, DomainKey_Signature:LONGTEXT, Organization:LONGTEXT, MIME_Version:DOUBLE, List_Unsubscribe:LONGTEXT, X_Received:LONGTEXT, X_Priority:LONGTEXT, X_MSMail_Priority:LONGTEXT, X_Mailer:LONGTEXT, X_MimeOLE:LONGTEXT, X_Notifications:LONGTEXT, X_Notification_ID:LONGTEXT, X_Sender_ID:LONGTEXT, X_Notification_Category:LONGTEXT, X_Notification_Type:LONGTEXT, X_UB:INT, Precedence:LONGTEXT, Reply_To:LONGTEXT, Auto_Submitted:LONGTEXT, Message_ID:LONGTEXT, Date:TIMESTAMP, Subject:LONGTEXT, From:LONGTEXT, To:LONGTEXT, Content_Type:LONGTEXT, Content:LONGTEXT, Attachments:LONGTEXT, SpamScore:DOUBLE, SpamReport:LONGTEXT, isSpam:TEXT

# Configuration for the SpamAssassin

SPAMD_HOST = '127.0.0.1'
SPAMD_PORT = 783
SPAMD_USER = 'spamd'
SPAMD_SPAMSCORELIMIT = 5.0
SPAMD_DOSPAMCHECK = False

import os,sys,traceback,shutil,pyzmail,recursive,tempfile,email.utils,datetime,socket

def process(file, config, rcontext, columns=None):
        fullpath = file.fullpath
        if "Message-ID: " not in open(fullpath,'r').read():
            return None
        # Try to parse rfc822 data
        try:
            #  Get the e-mail headers from a file
            email_file = open(fullpath, 'r')
            msg = pyzmail.PyzMessage.factory(email_file)

            # find all attachments and save them to a temp folder
            tempdir = None
            attachments = []
            try:
                tempdir = tempfile.mkdtemp(dir=config.EXTRACTDIR)
                for mailpart in msg.mailparts:

                    if not mailpart.is_body:
                        attachments.append(mailpart.filename)
                        f = open(os.path.join(tempdir, mailpart.filename), 'wb')
                        if mailpart.type.startswith('text/') and mailpart.charset is not None:
                            f.write(mailpart.get_payload().decode(mailpart.charset))
                        else:
                            f.write(mailpart.get_payload())
                        f.close()
                if len(attachments) > 0:
                    recursive.call_uforia_recursive(config, rcontext, tempdir, fullpath)
            except:
                traceback.print_exc(file=sys.stderr)
            finally:
                try:
                    if tempdir:
                        shutil.rmtree(tempdir)  # delete directory
                except OSError as exc:
                    traceback.print_exc(file=sys.stderr)
                    
            # Merge the receivers
            To = msg.get_decoded_header('To', None)
            XTo = msg.get_decoded_header('X-To', None)
            Cc = msg.get_decoded_header('Cc', None)
            XCc = msg.get_decoded_header('X-Cc', None)
            Bcc = msg.get_decoded_header('Bcc', None)
            XBcc = msg.get_decoded_header('X-Bcc', None)
            Date = datetime.datetime.fromtimestamp(int(email.utils.mktime_tz(email.utils.parsedate_tz(msg.get_decoded_header("Date", None))))).strftime('%Y-%m-%d %H:%M:%S')
            Subject = msg.get_decoded_header("Subject", None)
            From = msg.get_decoded_header("From", None)
            Received = msg.get_decoded_header("Received", None)
            MessageID = msg.get_decoded_header("Message-ID", None)
            Receivers = u''
            for i in [To,XTo,Cc,XCc,Bcc,XBcc]:
                if i:
                    Receivers += unicode(i)+', '

            # Get most common headers
            assorted = [msg.get_decoded_header("Delivered-To", None),
                        msg.get_decoded_header("Original-Recipient", None),
                        Received,
                        msg.get_decoded_header("Return-Path", None),
                        msg.get_decoded_header("Received-SPF", None),
                        msg.get_decoded_header("Authentication-Results", None),
                        msg.get_decoded_header("DKIM-Signature", None),
                        msg.get_decoded_header("DomainKey-Signature", None),
                        msg.get_decoded_header("Organization", None),
                        msg.get_decoded_header("MIME-Version", None),
                        msg.get_decoded_header("List-Unsubscribe", None),
                        msg.get_decoded_header("X-Received", None),
                        msg.get_decoded_header("X-Priority", None),
                        msg.get_decoded_header("X-MSMail-Priority", None),
                        msg.get_decoded_header("X-Mailer", None),
                        msg.get_decoded_header("X-MimeOLE", None),
                        msg.get_decoded_header("X-Notifications", None),
                        msg.get_decoded_header("X-Notification-ID", None),
                        msg.get_decoded_header("X-Sender-ID", None),
                        msg.get_decoded_header("X-Notification-Category", None),
                        msg.get_decoded_header("X-Notification-Type", None),
                        msg.get_decoded_header("X-UB", None),
                        msg.get_decoded_header("Precedence", None),
                        msg.get_decoded_header("Reply-To", None),
                        msg.get_decoded_header("Auto-Submitted", None),
                        MessageID,
                        Date,
                        Subject,
                        From,
                        Receivers,
                        msg.get_decoded_header("Content-Type", None)]

            # Grab the common headers and all E-mail bodies
            Body = ''
            Headers = {'From':From,'Subject':Subject,'To':To,'XTo:':XTo,'Cc':Cc,'XCc':XCc,'Bcc':Bcc,'XBcc':XBcc,'Date':Date,'MessageID':MessageID,'Received':Received}
            for key in Headers:
                if Headers[key]:
                    Body += key+': '+Headers[key]+'\n'
            Body += '\n'
            for mailpart in msg.mailparts:
                if mailpart.is_body:
                    payload = mailpart.get_payload()
                    try:
                        Body += payload.decode('utf-8')
                        Encoding = 'utf-8'
                    except UnicodeError:
                        try:
                            Body += payload.decode('ISO-8859-1')
                            Encoding = 'ISO-8859-1'
                        except UnicodeError:
                            Body += payload
            assorted.append(Body)

            assorted.append(','.join(attachments))

            # Spam checking code - R. Broerze & A. Hamed
            
            if SPAMD_DOSPAMCHECK:
                try:
                    raw_email = open(fullpath, 'r').read()
                    try:
                        full_email = raw_email.decode('utf-8')
                        Encoding = 'utf-8'
                    except UnicodeError:
                        try:
                            full_email = raw_email.decode('ISO-8859-1')
                            Encoding = 'ISO-8859-1'
                        except UnicodeError:
                            full_email = raw_email
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((SPAMD_HOST, SPAMD_PORT))
                    data =  'REPORT SPAMC/1.2\r\n'
                    data += 'Content-length: %d\r\n' % len(full_email.encode(Encoding))
                    data += 'User: %s\r\n\r\n' % SPAMD_USER
                    data += full_email
                    sock.sendall(data.encode(Encoding));
                    fd = sock.makefile('rb', 0)
                    spamd_header = fd.readline()
                    if spamd_header.find('EX_OK') == -1:
                        if config.DEBUG:
                            print('SpamCheck error')
                        traceback.print_exc(file=sys.stderr)
                        raise Exception
                    spamd_score = fd.readline()
                    spamd_score_splitted = spamd_score.split(";")[1].split("/")[0].strip()
                    saveReport = False
                    report = ''
                    for line in fd.readlines():
                        if saveReport:
                            report += line
                        if line.startswith('----'):
                            saveReport = True
                    assorted.append(spamd_score_splitted)
                    assorted.append(report)
                    if float(spamd_score_splitted) > SPAMD_SPAMSCORELIMIT:
                        assorted.append('yes')
                    else:
                        assorted.append('no')
                    sock.close()
                except Exception:
                    if config.DEBUG:
                        print('SpamCheck error')
                    traceback.print_exc(file=sys.stderr)
                    assorted.append(None);
                    assorted.append(None);
                    assorted.append('unknown');
            else:
                assorted.append(None);
                assorted.append(None);
                assorted.append('unknown');

            # Make sure we stored exactly the same amount of columns as
            # specified!!
            assert len(assorted) == len(columns)

            # Print some data that is stored in the database if debug is true
            if config.DEBUG:
                print "\nrfc822 file data:"
                for i in range(0, len(assorted)):
                    print "%-18s %s" % (columns[i] + ':', assorted[i])

            return assorted
        except TypeError:
            print('TypeError')
            pass
        except:
            traceback.print_exc(file=sys.stderr)

            # Store values in database so not the whole application crashes
            return None
