#!/bin/bash

# Parse CirrusSearch dump and insert pages to MediaWiki MySQL database
# USAGE: ./cirrus2mysql.sh /path/to/cirrus_dump.json

DB_SERVER="mysql"
DB_USER="mediawiki"
DB_PASSWORD="mediawiki"
DB_NAME="mediawiki"

#mysql_config_editor set --login-path=local --host=$DB_SERVER --user=$DB_USER --password=$DB_PASSWORD 

TS=`date +"%s"`

while IFS='' read -r line || [[ -n "$line" ]]; do
	if [ -z $action ]; then
		action=$line
	else
		# First line is "action" and second is "doc"
		# Extract page ID from action and page title from doc
		ID=`echo ${action} | jq -r '.index._id'`
		TITLE=`echo ${line} | jq -r '.title'`
		echo "id=$ID; title=$TITLE"

		#mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e 'SELECT COUNT(*) FROM page;' $DB_NAME
		#mysql --login-path=local -e 'SELECT COUNT(*) FROM page;' $DB_NAME

		mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e "INSERT INTO page SET page_id=$ID, page_title=\"$TITLE\", page_is_new=1, page_random=RAND(), page_touched=$TS, page_latest=105, page_content_model=\"wikitext\";" $DB_NAME
		mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e "INSERT INTO revision SET rev_id=$ID, rev_page=$ID, rev_text_id=$ID, rev_comment=\"CirrusSearch dump\", rev_user=1, rev_user_text=\"Admin\", rev_timestamp=$TS, rev_sha1=SHA1(\"$ID\");" $DB_NAME
		mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e "INSERT INTO text SET old_id=$ID, old_text=\"Dummy text for $TITLE\", old_flags=\"utf-8\";" $DB_NAME
		
		echo "---"
		#echo "INSERT INTO page SET page_id=$ID, page_title=\"$TITLE\", page_is_new=1, page_random=RAND(), page_touched=$TS, page_latest=105, page_content_model=\"wikitext\";"
		#echo "INSERT INTO text SET old_id=$ID, old_text=\"Dummy text for $TITLE\", old_flags=\"utf-8\";"
		#echo "INSERT INTO revision SET rev_id=$ID, rev_page=$ID, rev_text_id=$ID, rev_comment=\"CirrusSearch dump\", rev_user=1, rev_user_text=\"Admin\", rev_timestamp=$TS, rev_sha1=SHA1(\"$ID\");"


		unset action
	fi
done < "$1"

