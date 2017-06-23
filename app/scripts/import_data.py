#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import io
import json
import sys
import requests
import os.path
import time

offset = 2814900 # 2175000 # 4136800  # 0
batch_size = 100
remove_source_text = False # True
sleep_time = 5
sleep_n = 1000

flush_n = 10000
flush_time = 30
flush_url = 'http://localhost:9200/mediawiki_content_first/_flush'

es_url = 'http://localhost:9200/mediawiki_content_first/page/_bulk'

def send_flush():
    try:
        r = requests.post(flush_url)

    except requests.exceptions.RequestException, e:
        print("Failed to send update: " + str(e))

    if r.status_code != 200:
        print('ES Error: %s' % r.text)
    r.close()


def send_bulk(bulk_data):
    #print(bulk_data)
    #exit(0)
    try:
        r = requests.put(es_url, data=bulk_data)

    except requests.exceptions.RequestException, e:
        print("Failed to send update: " + str(e))

    if r.status_code != 200:
        print('ES Error: %s' % r.text)
    r.close()

def import_file(filename, counter=0, offset=0):
    if not os.path.exists(filename):
        print('File does not exist: %s' % filename)
        return
    elif not os.path.isfile(filename):
        print('Is not a valid file: %s' % filename)
        return

    batch_data = ''
    with io.open(filename, 'r', encoding='utf-8') as lines:
        for line in lines:
            if counter < offset:
                #print('Skip %i' % counter)
                counter += 1
                continue

            if counter % 2 == 0:
                # action line
                batch_data += line.encode('utf-8')
            else:
                # doc line
                if remove_source_text:
                    doc = json.loads(line)
                    doc['source_text'] = ''  # reomve source_text to save space

                    batch_data += json.dumps(doc) + '\n'
		else:
                    batch_data += line.encode('utf-8')

            counter += 1

            if counter % batch_size == 0:
                send_bulk(batch_data)
                batch_data = ''
                print('%s - %i (offset: %i)' % (datetime.datetime.now(), counter, offset))
                pass

            if counter % sleep_n == 0:
                time.sleep(sleep_time)

            if counter % flush_n == 0:
                send_flush()
                time.sleep(flush_time)

    if batch_data != '':
        send_bulk(batch_data)

    print('%s - done with %s' % (datetime.datetime.now(), filename))
    return counter

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Path to cirrus search dump is missing.')
        exit(1)

    counter = 0
    filename = sys.argv[1]

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


    print('done')
