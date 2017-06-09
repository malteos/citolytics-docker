#!/bin/bash

# Parse CirrusSearch dump and insert pages to MediaWiki MySQL database
# USAGE: ./cirrus2mysql.sh /path/to/cirrus_dump.json

DB_SERVER=$MEDIAWIKI_DB_SERVER
DB_USER="mediawiki" #$MEDIAWIKI_DB_USER
DB_PASSWORD="mediawiki" #$MEDIAWIKI_DB_USER
DB_NAME=$MEDIAWIKI_DB_NAME

export MYSQL_PWD=$DB_PASSWORD

#mysql_config_editor set --login-path=local --host=$DB_SERVER --user=$DB_USER --password=$DB_PASSWORD
mysql -u $DB_USER -h $DB_SERVER -e "DELETE FROM page WHERE page_id > 1; DELETE FROM revision WHERE rev_id > 1; DELETE FROM text WHERE old_id > 1;" $DB_NAME

TS=`date +"%s"`

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

                #echo "id=$ID; title=$TITLE"
                TEXT="Dummy text for $TITLE"
                LEN=${#TEXT}
                #mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e 'SELECT COUNT(*) FROM page;' $DB_NAME
                #mysql --login-path=local -e 'SELECT COUNT(*) FROM page;' $DB_NAME

                query_page="INSERT INTO page SET page_id=$ID, page_title=\"$TITLE\", page_is_new=1, page_random=RAND(), page_touched=$TS, page_links_updated=$TS, page_latest=$ID, page_len=$LEN, page_content_model=\"wikitext\";"
                query_rev="INSERT INTO revision SET rev_id=$ID, rev_page=$ID, rev_text_id=$ID, rev_comment=\"CirrusSearch dump\", rev_user=1, rev_user_text=\"Admin\", rev_timestamp=$TS, rev_len=$LEN, rev_parent_id=0, rev_sha1=SHA1(\"$ID\");"
                query_text="INSERT INTO text SET old_id=$ID, old_text=\"$TEXT\", old_flags=\"utf-8\";"

                mysql -u $DB_USER -h $DB_SERVER -e "$query_page$query_rev$query_text" $DB_NAME > /dev/null

                #mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e "INSERT INTO page SET page_id=$ID, page_title=\"$TITLE\", page_is_new=1, page_random=RAND(), page_touched=$TS, page_links_updated=$TS, page_latest=$ID, page_len=$LEN, page_content_model=\"wikitext\";" $DB_NAME
                #mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e "INSERT INTO revision SET rev_id=$ID, rev_page=$ID, rev_text_id=$ID, rev_comment=\"CirrusSearch dump\", rev_user=1, rev_user_text=\"Admin\", rev_timestamp=$TS, rev_len=$LEN, rev_parent_id=0, rev_sha1=SHA1(\"$ID\");" $DB_NAME
                #mysql -u $DB_USER -p$DB_PASSWORD -h $DB_SERVER -e "INSERT INTO text SET old_id=$ID, old_text=\"$TEXT\", old_flags=\"utf-8\";" $DB_NAME

                echo "--- $counter / $total"
                #echo "INSERT INTO page SET page_id=$ID, page_title=\"$TITLE\", page_is_new=1, page_random=RAND(), page_touched=$TS, page_latest=105, page_content_model=\"wikitext\";"
                #echo "INSERT INTO text SET old_id=$ID, old_text=\"Dummy text for $TITLE\", old_flags=\"utf-8\";"
                #echo "INSERT INTO revision SET rev_id=$ID, rev_page=$ID, rev_text_id=$ID, rev_comment=\"CirrusSearch dump\", rev_user=1, rev_user_text=\"Admin\", rev_timestamp=$TS, rev_sha1=SHA1(\"$ID\");"


                unset action
        fi
        ((counter++))
done < "$1"

export MYSQL_PWD=
