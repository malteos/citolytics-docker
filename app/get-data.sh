#!/bin/bash

set -e

: ${ES_HOST:=es}
: ${CIRRUS_DUMP_URL:=https://dumps.wikimedia.org/other/cirrussearch/20170529/simplewiki-20170529-cirrussearch-content.json.gz}
: ${CITOLYTICS_DUMP_URL:=http://citolytics-demo.wmflabs.org/dumps/citolytics_simplewiki.json.gz}
: ${BATCH_SIZE:=1000}


rm -fr $MEDIAWIKI_DIR/data
mkdir $MEDIAWIKI_DIR/data

# Download CirrusSearch dump, split the dump in chunks and send the data to Elasticsearch:

wget $CIRRUS_DUMP_URL -O $MEDIAWIKI_DIR/data/cirrus.json.gz
zcat $MEDIAWIKI_DIR/data/cirrus.json.gz > $MEDIAWIKI_DIR/data/cirrus.json
mkdir $MEDIAWIKI_DIR/data/cirrus.splits.d
split -l $BATCH_SIZE $MEDIAWIKI_DIR/data/cirrus.json $MEDIAWIKI_DIR/data/cirrus.splits.d/
for f in $MEDIAWIKI_DIR/data/cirrus.splits.d/{.,}*; do curl -XPOST $ES_HOST:9200/mediawiki_content_first/page/_bulk?pretty --data-binary @$f; done

# Popupate Citolytics data to ES

wget $CITOLYTICS_DUMP_URL -O citolytics.json
mkdir $MEDIAWIKI_DIR/data/citolytics.splits.d
split -l $BATCH_SIZE $MEDIAWIKI_DIR/data/citolytics.json $MEDIAWIKI_DIR/data/citolytics.splits.d/
for f in $MEDIAWIKI_DIR/data/citolytics.splits.d/{.,}*; do curl -XPOST $ES_HOST:9200/mediawiki_content_first/page/_bulk?pretty --data-binary @$f; done

# Clean up
rm -fr $MEDIAWIKI_DIR/data
