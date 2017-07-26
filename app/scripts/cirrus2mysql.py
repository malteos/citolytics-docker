#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import io
import json
import sys

import MySQLdb
from _mysql_exceptions import OperationalError

import time

db_host = '127.0.0.1'
db_user = 'mediawiki'
db_password = 'mediawiki'
db_name = 'mediawiki'

batch_size = 100

try:
    db = MySQLdb.connect(host=db_host,    # your host, usually localhost
                         user=db_user,         # your username
                         passwd=db_password,  # your password
                         db=db_name)
    cur = db.cursor()
except OperationalError:
    print('Error: Cannot connect to MySQL server')
    exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Path to cirrus search dump is missing.')
        exit(1)

    cirrus_filename = sys.argv[1]
    action_line = None
    doc_line = None
    counter = 1

    query_page = None
    query_rev = None
    query_text = None

    print('Start - deleting old pages...')

    cur.execute('DELETE FROM page WHERE page_id > 1')
    cur.execute('DELETE FROM revision WHERE rev_id > 1')
    cur.execute('DELETE FROM text WHERE old_id > 1')
    db.commit()

    print('Done - importing new pages...')

    with io.open(cirrus_filename, 'r', encoding='utf-8') as lines:
        for line in lines:
            if action_line is None:
                action_line = line
            else:
                doc_line = line
                action = json.loads(action_line)
                doc = json.loads(doc_line)

                id = action['index']['_id'].encode('utf-8')
                title = MySQLdb.escape_string(doc['title'].encode('utf-8').replace(' ', '_'))
                text = ""

                #text_len = str(len(text))
                ts = str(int(time.time()))

                page_values = "(" + id + ", \"" + title + "\", 1, RAND(), " + ts + ", " + ts + ", " + id + ", 0, \"wikitext\", \"0\", \"\")"
                rev_values = "(" + id + ", " + id + ", " + id + ", \"CirrusSearch dump\", 1, \"Admin\", " + \
                             ts + ", 0, 0, \"\")"
                # SHA1(\"" + id + "\")
                text_values = "(" + id + ", \"" + text + "\", \"utf-8\")"

                if query_page is None:
                    query_page = 'INSERT INTO page (page_id, page_title, page_is_new, page_random, page_touched, ' \
                                 'page_links_updated, page_latest, page_len, page_content_model, page_namespace, page_restrictions) VALUES ' + page_values
                else:
                    query_page += ', ' + page_values

                if query_rev is None:
                    query_rev = 'INSERT INTO revision (rev_id, rev_page, rev_text_id, rev_comment, rev_user, ' \
                                'rev_user_text, rev_timestamp, rev_len, rev_parent_id, rev_sha1) VALUES ' + rev_values
                else:
                    query_rev += ', ' + rev_values

                if query_text is None:

                    query_text = 'INSERT INTO text (old_id, old_text, old_flags) VALUES ' + text_values
                else:
                    query_text += ', ' + text_values

                if counter % batch_size == 0:
                    # send query
                    cur.execute(query_page)
                    cur.execute(query_rev)
                    cur.execute(query_text)
                    db.commit()

                    query_rev = None
                    query_page = None
                    query_text = None

                doc_line = None
                action_line = None

                print('%s - %i' % (datetime.datetime.now(), counter))
            counter += 1

    # TODO Compare COUNT(*) with counter
    #print('validating ...')

    print('done')
