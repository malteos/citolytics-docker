#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Citolytics - EventLogging Processor.

Usage:
    process_logs.py [--path=<path>] [--db-host=<hostname>] [--db-user=<username>] [--db-password=<password>] [--db-name=<database>] [--override] [--demo] [--verbose]
    process_logs.py (-h | --help)
    process_logs.py --version

Options:
    --db-host=<hostname>     DB hostname [default: mysql]
    --db-user=<username>     DB username [default: root]
    --db-password=<password>     DB user password [default: password]
    --db-name=<database>     Database [default: mediawiki]
    --path=<path>           Path to log file. [default: /var/log/nginx/events.log]
    --demo                  Generate random event log data
    --override                 Recreate tables before inserting new data
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
import io
import time

import dateutil.parser
from docopt import docopt
import MySQLdb
from _mysql_exceptions import OperationalError

class LogProcessor(object):
    def __init__(self):
        self.logger = logging.getLogger()
        #logging.config.fileConfig(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        #                                       'logging.conf'))


if __name__ == '__main__':
    args = docopt(__doc__, version='EventLogging Processor 0.0.1')

    try:
        db = MySQLdb.connect(host=args['--db-host'],    # your host, usually localhost
                         user=args['--db-user'],         # your username
                         passwd=args['--db-password'],  # your password
                         db=args['--db-name'])
        cur = db.cursor()
    except OperationalError:
        print('Error: Cannot connect to MySQL server')
        exit(1)

    proc = LogProcessor()

    def send_query(cur, query):

        if type(query) is tuple:
            # Query with args
            sql, args = query

            if args is None:
                cur.execute(sql)
            else:
                cur.execute(sql, args)

            return cur.rowcount
        elif type(query) is list:
            rowcount = 0
            for q in query:  # multiple queries
                rowcount += send_query(cur, q)
            return rowcount
        else:
            # Plain query (as string)
            cur.execute(query)
            return cur.rowcount

    def insert_MobileWikiAppArticleSuggestions(timestamp, event):
        if event['action'] == 'clicked' and 'readMoreIndex' in event:
            clickIndex = event['readMoreIndex']
        else:
            clickIndex = None # 'NULL'

        if event['action'] == 'shown' and 'latency' in event:
            latency = '%i' % event['latency']
        else:
            latency = 'NULL'

        readMoreList = event['readMoreList']

        queries = [
            ('INSERT INTO MobileWikiAppArticleSuggestions SET ' \
            '`timestamp`=%s, ' \
            '`pageTitle`=%s, ' \
            '`readMoreList`=%s, ' \
            '`readMoreIndex`=%s, ' \
            '`appInstallID`=%s, ' \
            '`readMoreSource`=%s, ' \
            '`action`=%s, ' \
            '`latency`=%s',

             (timestamp, event['pageTitle'], readMoreList, clickIndex, hashlib.md5(event['appInstallID']).hexdigest(), event['readMoreSource'], event['action'], latency)

             )
            ]


        if readMoreList != '':
            readMoreItems = readMoreList.split('|')
            for k, item in enumerate(readMoreItems):
                if event['action'] == 'clicked' and clickIndex == k:
                    clicked = 1
                else:
                    clicked = 0

                queries.append(
                    (
                        'INSERT INTO MobileWikiAppArticleSuggestions_items SET '
                        '`timestamp`=%s, `pageTitle`=%s, '
                        '`readMoreItem`=%s, `clicked`=%s, '
                        '`appInstallID`=%s, `readMoreSource`=%s, `action`=%s ',
                        (
                            timestamp, event['pageTitle'], item, clicked, hashlib.md5(event['appInstallID']).hexdigest(),
                            event['readMoreSource'], event['action']
                        )
                    )
                )
        return queries

    def insert_MobileWikiAppPageScroll(timestamp, event):
        return (
            'INSERT INTO MobileWikiAppPageScroll SET '
            '`timestamp`=%s, `pageID`=%s, `pageHeight`=%s, `maxPercentViewed`=%s, '
            '`appInstallID`=%s, `timeSpent`=%s',
            (
                timestamp, event['pageID'], event['pageHeight'], event['maxPercentViewed'],
                hashlib.md5(event['appInstallID']).hexdigest(), event['timeSpent']
            )
        )

    def insert_MobileWikiAppSessions(timestamp, event):
        return 'INSERT INTO MobileWikiAppSessions SET ' \
            '`timestamp`=%s, ' \
            '`appInstallID`=%s, ' \
            '`length`=%s, ' \
            '`totalPages`=%s, ' \
            '`fromSearch`=%s, ' \
            '`fromRandom`=%s, ' \
            '`fromLanglink`=%s, ' \
            '`fromInternal`=%s, ' \
            '`fromExternal`=%s, ' \
            '`fromHistory`=%s, ' \
            '`fromReadingList`=%s, ' \
            '`fromNearby`=%s, ' \
            '`fromDisambig`=%s, ' \
            '`fromBack`=%s', \
               (timestamp, hashlib.md5(event['appInstallID']).hexdigest(), event['length'], event['totalPages'],
                event['fromSearch'], event['fromRandom'], event['fromLanglink'], event['fromInternal'], event['fromExternal'],
                event['fromHistory'], event['fromReadingList'], event['fromNearby'], event['fromDisambig'], event['fromBack'])


    def insert_MobileAppShareAttempts(timestamp, event):
        return ('INSERT INTO MobileAppShareAttempts SET ' \
            '`timestamp`=%s, ' \
            '`username`=%s, ' \
            '`filename`=%s', (timestamp, hashlib.md5(event['username']).hexdigest(), event['filename']))

    schemas = {
        'MobileWikiAppArticleSuggestions': {
            'create_sql':
                'CREATE TABLE IF NOT EXISTS `MobileWikiAppArticleSuggestions` (' \
                    '`timestamp` DATETIME, ' \
                    '`action` ENUM("shown", "clicked"), ' \
                    '`readMoreList` VARCHAR(255), ' \
                    '`readMoreIndex` INT default NULL, ' \
                    '`readMoreSource` INT, ' \
                    '`latency` INT default NULL, ' \
                    '`appInstallID` VARCHAR(100) NOT NULL, ' \
                    '`pageTitle` VARCHAR(255) NOT NULL, ' \
                    'PRIMARY KEY(`timestamp`, `pageTitle`, `appInstallID`) )',
            'insert_sql': insert_MobileWikiAppArticleSuggestions
        },
        'MobileWikiAppArticleSuggestions_items': {
            'create_sql':
                'CREATE TABLE IF NOT EXISTS `MobileWikiAppArticleSuggestions_items` (' \
                    '`timestamp` DATETIME, ' \
                    '`action` ENUM("shown", "clicked"), ' \
                    '`readMoreItem` VARCHAR(255), ' \
                    '`clicked` TINYINT(1), ' \
                    '`readMoreSource` INT, ' \
                    '`appInstallID` VARCHAR(100) NOT NULL, ' \
                    '`pageTitle` VARCHAR(255) NOT NULL, ' \
                    'PRIMARY KEY(`timestamp`, `pageTitle`, `readMoreItem`, `appInstallID`) )'
        },
        'MobileWikiAppPageScroll': {
            'create_sql': 'CREATE TABLE IF NOT EXISTS `MobileWikiAppPageScroll` (' \
                '`timestamp` DATETIME, ' \
                '`pageID` INT NOT NULL, ' \
                '`pageHeight` INT NOT NULL, ' \
                '`maxPercentViewed` INT NOT NULL, ' \
                '`timeSpent` INT NOT NULL, ' \
                '`appInstallID` VARCHAR(100) NOT NULL, ' \
                'PRIMARY KEY (`timestamp`, `pageID`, `appInstallID`) '
                ')',
            'insert_sql': insert_MobileWikiAppPageScroll,
        },
        'MobileWikiAppSessions': {
            'create_sql': 'CREATE TABLE IF NOT EXISTS `MobileWikiAppSessions` (' \
                '`timestamp` DATETIME, ' \
                '`length` INT, ' \
                '`totalPages` INT, ' \
                '`fromSearch` INT, ' \
                '`fromRandom` INT, ' \
                '`fromLanglink` INT, ' \
                '`fromInternal` INT, ' \
                '`fromExternal` INT, ' \
                '`fromHistory` INT, ' \
                '`fromReadingList` INT, ' \
                '`fromNearby` INT, ' \
                '`fromDisambig` INT, ' \
                '`fromBack` INT, ' \
                '`appInstallID` VARCHAR(100) NOT NULL, ' \
                'PRIMARY KEY(`timestamp`, `appInstallID`) )',
            'insert_sql': insert_MobileWikiAppSessions
        },
        'MobileAppShareAttempts': {
            'create_sql': 'CREATE TABLE IF NOT EXISTS `MobileAppShareAttempts` (' \
                '`timestamp` DATETIME, ' \
                '`username` VARCHAR(255), ' \
                '`filename` VARCHAR(255), ' \
                'PRIMARY KEY(`timestamp`, `username`, `filename`) )',
            'insert_sql': insert_MobileAppShareAttempts
        }
    }

    if args['--verbose']:
        proc.logger.setLevel(logging.DEBUG)

    # format (from nginx config): '$time_iso8601|$query_string';

    log_path = args['--path'] # '/var/log/nginx/events.log'

    # Create event tables
    for schema_key in schemas:
        if args['--override']:
            send_query(cur, 'DROP TABLE IF EXISTS`' + schema_key + '`')

        send_query(cur, schemas[schema_key]['create_sql'])

    # Insert events
    print('Reading from: %s' % log_path)
    insert_counter = 0
    enc='utf-8'

    #with open(log_path, 'r', encoding=enc) as lines:
    with io.open(log_path, 'r', encoding=enc) as lines:
        for line in lines:
            cols = line.strip().split('|')

            #try:
            if len(cols) != 2:
                raise ValueError('Invalid column length')

            if cols[1] == '-':  # Ignore empty lines
                continue

            timestamp = dateutil.parser.parse(cols[0]).strftime('%Y-%m-%d %H:%M:%S')  # datetime.datetime.strptime(cols[0], "%Y-%m-%dT%H:%M:%S")
            event = json.loads(urllib.unquote(cols[1]))

            if event['schema'] not in schemas:
                continue

            schema = schemas[event['schema']]

            insert_counter += send_query(cur, schema['insert_sql'](timestamp, event['event']))
    db.commit()
    print('done. inserted %i rows' % insert_counter)


#except (KeyError, ValueError) as e:
#    raise ValueError('Invalid log line. Error: %s; Line: %s' % (e, line))
#print(cols)
