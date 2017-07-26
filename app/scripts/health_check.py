#!/usr/bin/python
"""Citolytics - EventLogging health check.

Usage:
    process_logs.py [--path=<path>] [--domain=<domain>] [--email=<email>] [--verbose]
    process_logs.py (-h | --help)
    process_logs.py --version

Options:
    --domain=<domain>     Domain to mediawiki [default: citolytics-simple.wmflabs.org]
    --path=<path>           Path to log file. [default: /var/log/nginx/events.log]
    --email=<email>           Send a message to this address in case of failure. [default: citolytics@i.mieo.de]
    --demo                  Generate random event log data
    --verbose               Show verbose debugging messages
    -h --help               Show this screen.
    --version               Show version.

"""
import logging
import logging.config
import json
import datetime
import urllib
import hashlib
import time
import requests
import yagmail
import os

from docopt import docopt
from sender import Mail

sleep_time = 3

def send_email(to_email, subject, body):
    if 'SMTP_LOGIN' in os.environ and 'SMTP_PASSWORD' in os.environ:
        mail = Mail("fiq.de", port=25, username=os.environ['SMTP_LOGIN'], password=os.environ['SMTP_PASSWORD'], use_tls=False, use_ssl=False, debug_level=None)
        mail.send_message(subject, fromaddr="citolytics@i.mieo.de", to=to_email, body=body)
    else:
        print('Cannot send email. SMTP_LOGIN and SMTP_PASSWORD not set.')

# From: https://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
def tail( f, lines=20 ):
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                # from the end of the file
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            # read the last block we haven't yet read
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count('\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = ''.join(reversed(blocks))
    return '\n'.join(all_read_text.splitlines()[-total_lines_wanted:])

if __name__ == '__main__':
    args = docopt(__doc__, version='EventLogging health check 0.1')

    email_to = args['--email']
    log_path = args['--path']
    el_url = 'http://' + args['--domain'] + '/beacon/event'
    event_id = 'CHECKID_' + str(time.time())
    event = {
        'schema': 'healthCheck',
        'id': event_id
    }

    res = requests.get(el_url + '?' + json.dumps(event))

    try:

        if res.status_code == 204:
            time.sleep(sleep_time)

            last_lines = tail(open(log_path))

            if event_id in last_lines:
                pass
            else:
                raise ValueError('EventId not found in log')
        else:
            raise ValueError('Invalid response code from beacon: %i' % res.status_code)
    except ValueError as e:
        msg = 'Error: %s' % e
        send_email(email_to, 'Citolytics: Test failed', msg)
        print(msg)
        exit(1)

    print('Test OK')
