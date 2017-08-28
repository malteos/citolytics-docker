#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Citolytics - Import ES bulk.

Import Citolytics and CirrusSearch dump (ES bulk format) to CirruSearch index.

Usage:
    import_data.py [--path=<path>] [--host=<host>] [--offset=<offset>] [--sleep=<seconds>] [--flush=<seconds>] [--verbose]
    import_data.py (-h | --help)
    import_data.py --version

Options:
    --host=<host>     Domain to ES [default: localhost]
    --path=<path>           Path to log file. [default: citolytics.json]
    --sleep=<seconds>       Wait after 1000 items in seconds [default: 5]
    --flush=<seconds>       Wait after flush in seconds [default: 30]
    --offset=<offset>           Offset. [default: 0]
    --verbose               Show verbose debugging messages
    -h --help               Show this screen.
    --version               Show version.

Notes:
    - Empty ES index: $ curl -XPOST es:9200/mediawiki_content_first/page/_delete_by_query?pretty -d '{"query": {"match_all": {}}}'
    - Count docs: $ curl -XPOST es:9200/mediawiki_content_first/page/_count?pretty

    - Wiki pages
        - dewiki:       2.084.811
            - mysql:    2.066.400
            - es:       2.068.443
            - import
                - update (json=2.012.009)

        - simplewiki:   126.731
            - mysql:    125.186
            - es:       125.235
            - json:     125.235
            - import
                - index -- Success: 125.235, Errors: 0
                - update -- Success: 121.847, Errors: 59

"""
import datetime
import io
import json
import sys
import requests
import os.path
import time
import subprocess
from docopt import docopt

#offset = 2814900 # 2175000 # 4136800  # 0
batch_size = 500 # 40
remove_source_text = True # False # True
sleep_time = 5
sleep_n = 2500
enable_es_restart = False

flush_n = 10000
flush_time = 30

es_host = 'localhost'

def restart_es():
    es = subprocess.Popen(["service", "elasticsearch", "restart"], stdout=subprocess.PIPE)
    res = es.communicate()[0]

    if 'error' in res or 'ERROR' in res:
        print('Could not restart ES: %s' % res)
	exit(1)
    else:
        print('ES restarted')

def send_flush():
    flush_url = 'http://' + es_host + ':9200/mediawiki_content_first/_flush'

    try:
        r = requests.post(flush_url)

        if r.status_code != 200:
            print('ES Error (flush): %s' % r.text)
    except requests.exceptions.RequestException, e:
        print("Failed to send flush: " + str(e))
        exit(1)

    r.close()


def send_bulk(bulk_data):
    es_url = 'http://' + es_host + ':9200/mediawiki_content_first/page/_bulk'

    error_count = 0
    success_count = 0
    response = ''

    #bulk_data = bulk_data.decode('utf-8')
    #print(bulk_data)
    #exit(0)
    try:
        r = requests.put(es_url, data=bulk_data)

        if r.status_code == 200:
            response = r.text
            res = json.loads(response)
            # parse response

            for item in res['items']:
                if 'update' in item:
                    action = item['update']
                elif 'index' in item:
                    action = item['index']
                else:
                    print('Unknown action response: %s' % item)
                    exit(1)

                if action['status'] == 200 or action['status'] == 201:
                    success_count += 1
                elif action['status'] >= 500:
                    print('Server error: %s' % action)
                    exit(1)
                else:
                    error_count += 1
                    print('Error - status=%i, page_id=%s' % (action['status'], action['_id']))

                    if action['status'] != 404:
                        print('Other error: %s' % action)

        else:
            print('ES Error: %s;\nRequest:' % (r.text))
            #print(bulk_data)

    except requests.exceptions.RequestException, e:
        print("Failed to send bulk: " + str(e))
        exit(1)

    r.close()

    return response, success_count, error_count

def import_file(filename, counter=0, offset=0):
    if not os.path.exists(filename):
        print('File does not exist: %s' % filename)
        return
    elif not os.path.isfile(filename):
        print('Is not a valid file: %s' % filename)
        return

    total_success_count = 0
    total_error_count = 0
    enc='utf-8'
    #enc='iso-8859-15'
    batch_data = ''
    with io.open(filename, 'r', encoding=enc) as lines: # , encoding='utf-8')
        for line in lines:
            #print(line)
            #continue

            if counter < offset:
                #print('Skip %i' % counter)
                counter += 1
                continue

            if counter % 2 == 0:
                # action line
                batch_data += line.encode(enc) #.encode('utf-8')
            else:
                # doc line
                if remove_source_text:
                    doc = json.loads(line)

                    if 'source_text' in doc:
                        doc['source_text'] = ''  # reomve source_text to save space

                    batch_data += json.dumps(doc) + '\n'
		else:
                    batch_data += line.encode(enc) #.encode('utf-8')

            counter += 1

            if counter % batch_size == 0:
                res, success_count, error_count = send_bulk(batch_data)
                total_success_count += success_count
                total_error_count += error_count

                batch_data = ''
                print('%s - %i (offset: %i)' % (datetime.datetime.now(), counter, offset))
                pass

            if counter % sleep_n == 0:
                time.sleep(sleep_time)

            if counter % flush_n == 0:
                send_flush()
                time.sleep(flush_time)


            if enable_es_restart and counter % (flush_n * 3) == 0:
                restart_es()
                time.sleep(flush_time * 3)

    if batch_data != '':
        res, success_count, error_count = send_bulk(batch_data)
        total_success_count += success_count
        total_error_count += error_count

    print('%s - done with %s' % (datetime.datetime.now(), filename))
    print('-- Success: %i, Errors: %i' % (total_success_count, total_error_count))

    return counter


if __name__ == '__main__':
    args = docopt(__doc__, version='Import Data ES 0.1')

    counter = 0
    filename = args['--path']
    offset = int(args['--offset'])
    es_host = args['--host']
    flush_time = int(args['--flush'])
    sleep_time = int(args['--sleep'])

    print('Starting ...')

    if not os.path.exists(filename):
        print('File does not exist: %s' % filename)
        exit(1)
    elif os.path.isfile(filename):
        import_file(filename, offset=offset)
    elif os.path.isdir(filename):
        print('Input is a directory')
        for f in os.path.listdir(filename):
            file_counter = import_file(os.path.join(filename, f), counter, offset=offset)
            counter += file_counter

    exit(0)
