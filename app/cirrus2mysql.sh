#!/bin/bash

# Parse CirrusSearch dump and insert pages to MediaWiki MySQL database
# USAGE: ./cirrus2mysql.sh /path/to/cirrus_dump.json

DB_SERVER=$MEDIAWIKI_DB_SERVER
DB_USER="mediawiki" #$MEDIAWIKI_DB_USER
DB_PASSWORD="mediawiki" #$MEDIAWIKI_DB_USER
DB_NAME=$MEDIAWIKI_DB_NAME
BATCH_SIZE=50

export MYSQL_PWD=$DB_PASSWORD

mysql -u $DB_USER -h $DB_SERVER -e "DELETE FROM page WHERE page_id > 1; DELETE FROM revision WHERE rev_id > 1; DELETE FROM text WHERE old_id > 1;" $DB_NAME

TS=`date +"%s"` # TODO MediaWiki does not use unix timestamp

counter=1
total=`cat $1 | wc -l`

while IFS='' read -r line || [[ -n "$line" ]]; do
        if [ -z $action ]; then
                action=$line
        else
                # First line is "action" and second is "doc"
                # Extract page ID from action and page title from doc
                ID=`echo ${action} | jq -r '.index._id'`
                TITLE=`echo ${line} | jq -r '.title'`
                TITLE=${TITLE// /_} # replace whitespaces with underscores
                TITLE=$(printf '%q' $TITLE) # escape double quotes

                TEXT="Dummy text for $TITLE"
                LEN=${#TEXT}

                page_values="($ID, \"$TITLE\", 1, RAND(), $TS, $TS, $ID, $LEN, \"wikitext\")"
                rev_values="($ID, $ID, $ID, \"CirrusSearch dump\", 1, \"Admin\", $TS, $LEN, 0, SHA1(\"$ID\"))"
                text_values="($ID, \"$TEXT\", \"utf-8\")"

                if [ -z "$query_page" ]; then
                        query_page="INSERT INTO page (page_id, page_title, page_is_new, page_random, page_touched, page_links_updated, page_latest, page_len, page_content_model) VALUES $page_values"
                else
                        query_page="$query_page, $page_values"
                fi

                if [ -z "$query_rev" ]; then
                        query_rev="INSERT INTO revision (rev_id, rev_page, rev_text_id, rev_comment, rev_user, rev_user_text, rev_timestamp, rev_len, rev_parent_id, rev_sha1) VALUES $rev_values"
                else
                        query_rev="$query_rev, $rev_values"
                fi

                if [ -z "$query_text" ]; then
                        query_text="INSERT INTO text (old_id, old_text, old_flags) VALUES $text_values"
                else
                        query_text="$query_text, $text_values"
                fi

                if ! ((counter % $BATCH_SIZE)); then
                        mysql -u $DB_USER -h $DB_SERVER -e "$query_page; $query_rev; $query_text" $DB_NAME
                        unset query_page
                        unset query_rev
                        unset query_text
                fi

                echo "--- $counter / $total"
                unset action
        fi
        ((counter++))
done < "$1"

# Last batch
if ! [ -z "$query_rev" ]; then
        mysql -u $DB_USER -h $DB_SERVER -e "$query_page; $query_rev; $query_text" $DB_NAME
fi

export MYSQL_PWD=
