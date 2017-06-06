#!/bin/bash

# Print commands
set -e

: ${MEDIAWIKI_SITE_NAME:=CitolyticsDemo}
: ${MEDIAWIKI_SITE_SCRIPTPATH:=/mediawiki}
: ${MEDIAWIKI_ADMIN_USER:=admin}
: ${MEDIAWIKI_ADMIN_PASS:=citolytics}
: ${MEDIAWIKI_DB_SERVER:=mysql}
: ${MEDIAWIKI_DB_NAME:=mediawiki}
: ${MEDIAWIKI_DB_USER:=root}
: ${MEDIAWIKI_DB_PASSWORD:=password}

#mkdir -p $MEDIAWIKI_DIR

if [ -d "$MEDIAWIKI_DIR" ]; then
  # Control will enter here if $DIRECTORY exists.
  rm -fr $MEDIAWIKI_DIR/*
  rm -fr $MEDIAWIKI_DIR/.git/
  #rm -fr $MEDIAWIKI_DIR/.* 2> /dev/null
fi

# Install Mediawiki core
git clone -b $MEDIAWIKI_BRANCH https://gerrit.wikimedia.org/r/p/mediawiki/core.git $MEDIAWIKI_DIR
cd $MEDIAWIKI_DIR
composer install --no-dev

# Download skins
cd $MEDIAWIKI_DIR
array=( Modern Vector )
for EXT in "${array[@]}"
do
  if [ ! -d "/var/www/public/mediawiki/extensions/$EXT" ];then
  	git clone -b $MEDIAWIKI_BRANCH https://gerrit.wikimedia.org/r/p/mediawiki/skins/$EXT $MEDIAWIKI_DIR/skins/$EXT
    cd $MEDIAWIKI_DIR/skins/$EXT && composer install --no-dev
    cd $MEDIAWIKI_DIR
  fi
done

# Download extensions
cd $MEDIAWIKI_DIR
array=( Elastica CirrusSearch PageImages MobileApp MobileFrontend Wikibase EventLogging )
for EXT in "${array[@]}"
do
  if [ ! -d "/var/www/public/mediawiki/extensions/$EXT" ];then
  	git clone -b $MEDIAWIKI_BRANCH https://gerrit.wikimedia.org/r/p/mediawiki/extensions/$EXT $MEDIAWIKI_DIR/extensions/$EXT
    cd $MEDIAWIKI_DIR/extensions/$EXT && composer install --no-dev
    cd $MEDIAWIKI_DIR
  fi
done

# EventLogging server
cd $MEDIAWIKI_DIR/extensions/EventLogging/server && git submodule update --init

# Execute install script
php $MEDIAWIKI_DIR/maintenance/install.php \
	--dbname "$MEDIAWIKI_DB_NAME" \
	--dbserver "$MEDIAWIKI_DB_SERVER" \
	--dbuser "$MEDIAWIKI_DB_USER" \
	--dbpass "$MEDIAWIKI_DB_PASSWORD" \
	--pass "$MEDIAWIKI_ADMIN_PASS" \
  --scriptpath "$MEDIAWIKI_SITE_SCRIPTPATH" \
	"$MEDIAWIKI_SITE_NAME" \
	"$MEDIAWIKI_ADMIN_USER"


echo "@include('$WEBROOT/CustomSettings.php');" >> $MEDIAWIKI_DIR/LocalSettings.php

# CirrusSearch
# curl -XDELETE es:9200/mediawiki_content_first; curl -XDELETE es:9200/mediawiki_general_first;
# TODO exit code 1
php $MEDIAWIKI_DIR/extensions/CirrusSearch/maintenance/updateSearchIndexConfig.php || echo "CirrusSearch failed (1). Try to update mapping settings"
curl -XPUT 'http://es:9200/_all/_settings?preserve_existing=true' -d '{"index.mapping.total_fields.limit" : "2000"}'
php $MEDIAWIKI_DIR/extensions/CirrusSearch/maintenance/updateSearchIndexConfig.php || echo "CirrusSearch failed (2). Try to update mapping settings"
curl -XPUT 'http://es:9200/_all/_settings?preserve_existing=true' -d '{"index.mapping.total_fields.limit" : "2000"}'
php $MEDIAWIKI_DIR/extensions/CirrusSearch/maintenance/updateSearchIndexConfig.php || echo "CirrusSearch failed (3). Something else went wrong."

php $MEDIAWIKI_DIR/extensions/CirrusSearch/maintenance/forceSearchIndex.php --skipLinks --indexOnSkip
php $MEDIAWIKI_DIR/extensions/CirrusSearch/maintenance/forceSearchIndex.php --skipParse

# WikiBase
php $MEDIAWIKI_DIR/maintenance/update.php --quick
php $MEDIAWIKI_DIR/extensions/Wikibase/lib/maintenance/populateSitesTable.php
php $MEDIAWIKI_DIR/extensions/Wikibase/client/maintenance/populateInterwiki.php
