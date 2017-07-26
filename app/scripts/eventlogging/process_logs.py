#!/usr/bin/python
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
        if isinstance(query, basestring):
            cur.execute(query)
            return cur.rowcount
        else:
            rowcount = 0
            for q in query:  # multiple queries
                cur.execute(q)
                rowcount += cur.rowcount
            return rowcount

    def insert_MobileWikiAppArticleSuggestions(timestamp, event):
        if event['action'] == 'clicked' and 'readMoreIndex' in event:
            clickIndex = event['readMoreIndex']
        else:
            clickIndex = 'NULL'

        if event['action'] == 'shown' and 'latency' in event:
            latency = '%i' % event['latency']
        else:
            latency = 'NULL'

        readMoreList = event['readMoreList']

        queries = [
            'INSERT INTO MobileWikiAppArticleSuggestions SET ' \
            '`timestamp`="' + timestamp + '", ' \
            '`pageTitle`="' + str(event['pageTitle']) + '", ' \
            '`readMoreList`="' + readMoreList + '", ' \
            '`readMoreIndex`=' + str(clickIndex) + ', ' \
            '`appInstallID`="' + hashlib.md5(event['appInstallID']).hexdigest() + '", ' \
            '`readMoreSource`="' + str(event['readMoreSource']) + '", ' \
            '`action`="' + str(event['action']) + '", ' \
            '`latency`=' + latency + ''
            ]

        if readMoreList != '':
            readMoreItems = readMoreList.split('|')
            for k, item in enumerate(readMoreItems):
                if event['action'] == 'clicked' and clickIndex == k:
                    clicked = 1
                else:
                    clicked = 0

                queries.append(
                    'INSERT INTO MobileWikiAppArticleSuggestions_items SET ' \
                                '`timestamp`="' + timestamp + '", ' \
                                '`pageTitle`="' + str(event['pageTitle']) + '", ' \
                                '`readMoreItem`="' + item + '", ' \
                                '`clicked`=' + str(clicked) + ', ' \
                                '`appInstallID`="' + hashlib.md5(event['appInstallID']).hexdigest() + '", ' \
                                '`readMoreSource`="' + str(event['readMoreSource']) + '", ' \
                                '`action`="' + str(event['action']) + '" '
                                )
        return queries

    def insert_MobileWikiAppPageScroll(timestamp, event):
        return 'INSERT INTO MobileWikiAppPageScroll SET ' \
            '`timestamp`="' + timestamp + '", ' \
            '`pageID`="' + str(event['pageID']) + '", ' \
            '`pageHeight`="' + str(event['pageHeight']) + '", ' \
            '`maxPercentViewed`="' + str(event['maxPercentViewed']) + '", ' \
            '`appInstallID`="' + hashlib.md5(event['appInstallID']).hexdigest() + '", ' \
            '`timeSpent`="' + str(event['timeSpent']) + '"'

    def insert_MobileWikiAppSessions(timestamp, event):
        return 'INSERT INTO MobileWikiAppSessions SET ' \
            '`timestamp`="' + timestamp + '", ' \
            '`appInstallID`="' + hashlib.md5(event['appInstallID']).hexdigest() + '", ' \
            '`length`="' + str(event['length']) + '", ' \
            '`totalPages`="' + str(event['totalPages']) + '", ' \
            '`fromSearch`="' + str(event['fromSearch']) + '", ' \
            '`fromRandom`="' + str(event['fromRandom']) + '", ' \
            '`fromLanglink`="' + str(event['fromLanglink']) + '", ' \
            '`fromInternal`="' + str(event['fromInternal']) + '", ' \
            '`fromExternal`="' + str(event['fromExternal']) + '", ' \
            '`fromHistory`="' + str(event['fromHistory']) + '", ' \
            '`fromReadingList`="' + str(event['fromReadingList']) + '", ' \
            '`fromNearby`="' + str(event['fromNearby']) + '", ' \
            '`fromDisambig`="' + str(event['fromDisambig']) + '", ' \
            '`fromBack`="' + str(event['fromBack']) + '"'

    def insert_MobileAppShareAttempts(timestamp, event):
        return 'INSERT INTO MobileAppShareAttempts SET ' \
            '`timestamp`="' + timestamp + '", ' \
            '`username`="' + hashlib.md5(event['username']).hexdigest() + '", ' \
            '`filename`="' + str(event['filename']) + '"'

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
            send_query(cur, 'DROP TABLE `' + schema_key + '`')

        send_query(cur, schemas[schema_key]['create_sql'])

    # Insert events
    print('Reading from: %s' % log_path)
    insert_counter = 0
    with open(log_path, 'r') as lines:
        for line in lines:
            cols = line.strip().split('|')

            try:
                if len(cols) != 2:
                    raise ValueError('Invalid column length')

                timestamp = cols[0] # datetime.datetime.strptime(cols[0], "%Y-%m-%dT%H:%M:%S")
                event = json.loads(urllib.unquote(cols[1]))

                if event['schema'] not in schemas:
                    continue

                schema = schemas[event['schema']]

                insert_counter += send_query(cur, schema['insert_sql'](timestamp, event['event']))

            except (KeyError, ValueError) as e:
                raise ValueError('Invalid log line. Error: %s; Line: %s' % (e, line))

            #print(cols)
    db.commit()
    print('done. inserted %i rows' % insert_counter)
