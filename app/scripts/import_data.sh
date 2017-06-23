#!/bin/bash


# wiki=de
# export CIRRUS_DUMP_URL="https://dumps.wikimedia.org/other/cirrussearch/20170529/dewiki-20170529-cirrussearch-content.json.gz"
# export CITOLYTICS_DUMP_URL="http://citolytics-demo.wmflabs.org/dumps/citolytics_dewiki.json.gz"
#
# wiki=en
# export CIRRUS_DUMP_URL="https://dumps.wikimedia.org/other/cirrussearch/20170529/enwiki-20170529-cirrussearch-content.json.gz"
# export CITOLYTICS_DUMP_URL="http://citolytics-demo.wmflabs.org/dumps/citolytics_enwiki.json.gz"

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

# $MEDIAWIKI_DIR/cirrus2mysql.sh $MEDIAWIKI_DIR/data/cirrus.json
/cirrus2mysql.sh $MEDIAWIKI_DIR/data/cirrus.json

# Popupate Citolytics data to ES

wget $CITOLYTICS_DUMP_URL -O $MEDIAWIKI_DIR/data/citolytics.json.gz
zcat $MEDIAWIKI_DIR/data/citolytics.json.gz > $MEDIAWIKI_DIR/data/citolytics.json
mkdir $MEDIAWIKI_DIR/data/citolytics.splits.d
split -l $BATCH_SIZE $MEDIAWIKI_DIR/data/citolytics.json $MEDIAWIKI_DIR/data/citolytics.splits.d/
for f in $MEDIAWIKI_DIR/data/citolytics.splits.d/{.,}*; do curl -XPOST $ES_HOST:9200/mediawiki_content_first/page/_bulk?pretty --data-binary @$f; done

# Clean up
rm -fr $MEDIAWIKI_DIR/data