"""

Data extraction for event logging evaluation

tables: MobileWikiAppArticleSuggestions (), MobileWikiAppArticleSuggestions_items, MobileWikiAppPageScroll, MobileWikiAppSessions

extract page ids (already in mediawiki table)

## long CTR

### details
SELECT i.appInstallID, i.pageTitle, i.readMoreItem, i.clicked, s.maxPercentViewed, s.timeSpent, i.timestamp, TIMEDIFF(s.timestamp, i.timestamp)
FROM MobileWikiAppArticleSuggestions_items i
JOIN page p ON p.page_title = REPLACE( i.readMoreItem, " ", "_")
JOIN MobileWikiAppPageScroll s
    ON s.pageID = p.page_id
    AND s.appInstallID = i.appInstallID
    AND s.timestamp > i.timestamp
    AND TIMEDIFF(s.timestamp, i.timestamp) < 600;

### summary (min timespent 10)

SELECT y.readMoreSource, SUM(y.clicked)  as longClicks, AVG(y.timeSpent) as avgTimeSpent, AVG(y.maxPercentViewed) as avgMaxPercentViewed
FROM (
SELECT i.readMoreSource, i.pageTitle, i.clicked, x.*, COUNT(*), TIMEDIFF(x.timestamp, i.timestamp)
FROM MobileWikiAppArticleSuggestions_items i
JOIN (
    SELECT p.page_title, s.appInstallID, s.timestamp, s.timeSpent, s.maxPercentViewed
    FROM page p
    JOIN MobileWikiAppPageScroll s
        ON s.pageID = p.page_id
    GROUP BY p.page_id, s.appInstallID, s.timestamp
    ) x
    ON x.page_title = REPLACE( i.readMoreItem, " ", "_")
    AND x.appInstallID = i.appInstallID
WHERE i.clicked = 1
    AND x.timestamp > i.timestamp
    AND TIMEDIFF(x.timestamp, i.timestamp) < 600
    AND timeSpent > 10
GROUP BY i.appInstallID, i.timestamp
) y
GROUP BY y.readMoreSource;

### old
ELECT i.readMoreSource, SUM(i.clicked) as longClicks, AVG(s.timeSpent) as avgTimeSpent, AVG(s.maxPercentViewed) as avgMaxPercentViewed
FROM MobileWikiAppArticleSuggestions_items i
LEFT JOIN page p
    ON p.page_title = REPLACE( i.readMoreItem, " ", "_")
LEFT JOIN MobileWikiAppPageScroll s
    ON s.pageID = p.page_id
    AND s.appInstallID = i.appInstallID
    AND s.timestamp > i.timestamp
    AND TIMEDIFF(s.timestamp, i.timestamp) < 600
WHERE i.clicked = 1
GROUP BY i.readMoreSource;

SELECT i.readMoreSource, SUM(i.clicked) as longClicks, COUNT(*)
FROM MobileWikiAppArticleSuggestions_items i
WHERE i.clicked = 1
GROUP BY i.readMoreSource;


## sessions stats
### group 10min sessions per user

SELECT x.readMoreSource, COUNT(*) as sessionCount, SUM(x.totalPages) as totalPages, AVG(x.totalPages) as avgTotalPages,
    AVG(x.length) as avgLength, AVG(x.fromSearch) as avgFromSearch, AVG(x.fromRandom) as avgFromRandom, AVG(x.fromInternal) as avgFromInternal, AVG(x.fromBack) as avgFromBack
FROM (
    SELECT i.readMoreSource, i.appInstallID, s.length, s.totalPages, s.fromSearch, s.fromRandom, s.fromInternal, s.fromBack,
        s.timestamp, ROUND(TIMEDIFF(NOW(), s.timestamp) / 600) as sessionTime
    FROM MobileWikiAppSessions s
    JOIN MobileWikiAppArticleSuggestions i
        ON i.appInstallID = s.appInstallID

    GROUP BY ROUND(TIMEDIFF(NOW(), s.timestamp) / 600)
    ORDER BY s.appInstallID, s.timestamp
) as x
GROUP BY x.readMoreSource;

"""
import numpy as np
import pandas as pd
import MySQLdb
#from tabulate import tabulate
from _mysql_exceptions import OperationalError

read_more_sources = {
    1: 'MLT', # or 2
    2: 'Citolytics'
}

read_more_source_mlt = 1 # or 2
read_more_source_citolytics = 3

class ELEvaluation(object):
    def __init__(self, db_host, db_user, db_password, db_name):
        try:
            self.db = MySQLdb.connect(host=db_host,    # your host, usually localhost
                                 user=db_user,         # your username
                                 passwd=db_password,  # your password
                                 db=db_name)
            self.cur = self.db.cursor(MySQLdb.cursors.DictCursor)

        except OperationalError:
            print('Error: Cannot connect to MySQL server')
            exit(1)

    def set_read_more_source_label(self, df):
        df['readMoreSource'] = df.apply(lambda r: read_more_sources[int(r['readMoreSource'])], axis=1)

        return df

    def get_event_time_series(self, table='MobileWikiAppArticleSuggestions'):
        sql = 'SELECT `timestamp`, COUNT(*) as `count`' \
                + ' FROM ' + table \
                + ' GROUP BY DATE_FORMAT(`timestamp`, "%Y-%m-%d %H:00:00")  ORDER BY `timestamp`'
        self.cur.execute(sql)

        datetimes = []
        counts = []
        for r in self.cur.fetchall():
            #print(r)
            datetimes.append(r['timestamp'])
            counts.append([r['count']])

        return datetimes, counts

    def get_most_recommended_items(self, limit=10):
        return pd.read_sql('SELECT readMoreItem, COUNT(*) as views FROM MobileWikiAppArticleSuggestions_items WHERE clicked = 0 GROUP BY readMoreItem ORDER BY COUNT(*) DESC LIMIT %i' % limit, con=self.db)

    def get_most_clicked_items(self, limit=10):
        return pd.read_sql('SELECT readMoreItem, COUNT(*) as clicks FROM MobileWikiAppArticleSuggestions_items WHERE clicked = 1 GROUP BY readMoreItem ORDER BY COUNT(*) DESC LIMIT %i' % limit, con=self.db)

    def get_stats_per_source(self):
        # views divided by 3?
        df = pd.read_sql('SELECT readMoreSource, SUM(clicked) as clicks, COUNT(*) as views, SUM(clicked) / COUNT(*) as ctr ' \
            ' FROM MobileWikiAppArticleSuggestions_items' \
            ' GROUP BY readMoreSource', con=self.db)

        return self.set_read_more_source_label(df)

    def get_long_stats_per_source(self, minTimeSpent=10, minPercentViewed=50):
        # join with views?
        sql = 'SELECT y.readMoreSource, SUM(y.clicked)  as longClicks, AVG(y.timeSpent) as avgTimeSpent, AVG(y.maxPercentViewed) as avgMaxPercentViewed' \
            ' FROM (' \
            ' SELECT i.readMoreSource, i.pageTitle, i.clicked, x.*, COUNT(*), TIMEDIFF(x.timestamp, i.timestamp)' \
            ' FROM MobileWikiAppArticleSuggestions_items i' \
            ' JOIN (' \
            '     SELECT p.page_title, s.appInstallID, s.timestamp, s.timeSpent, s.maxPercentViewed' \
            '     FROM page p' \
            '     JOIN MobileWikiAppPageScroll s' \
            '         ON s.pageID = p.page_id' \
            '     GROUP BY p.page_id, s.appInstallID, s.timestamp' \
            '     ) x' \
            '     ON x.page_title = REPLACE( i.readMoreItem, " ", "_")' \
            '     AND x.appInstallID = i.appInstallID' \
            ' WHERE i.clicked = 1' \
            '     AND x.timestamp > i.timestamp' \
            '     AND TIMEDIFF(x.timestamp, i.timestamp) < 600'

        if minTimeSpent > 0:
            sql += ' AND timeSpent > %i' % minTimeSpent

        if minPercentViewed > 0:
            sql += ' AND maxPercentViewed > %i' % minPercentViewed

        sql += ' GROUP BY i.appInstallID, i.timestamp' \
            ' ) y' \
            ' GROUP BY y.readMoreSource'

        df = pd.read_sql(sql, con=self.db)

        return self.set_read_more_source_label(df)

    def get_session_stats(self):
        return pd.read_sql('SELECT COUNT(*), SUM(length), SUM(totalPages), SUM(fromRandom), SUM(fromSearch, AVG(length), AVG(totalPages), AVG(fromRandom), AVG(fromSearch) FROM MobileWikiAppSessions', con=self.db)

    def get_session_stats_per_source(self):
        sql = 'SELECT x.readMoreSource, COUNT(*) as sessionCount, SUM(x.totalPages) as totalPages, AVG(x.totalPages) as avgTotalPages,' \
            ' AVG(x.length) as avgLength, AVG(x.fromSearch) as avgFromSearch, AVG(x.fromRandom) as avgFromRandom, AVG(x.fromInternal) as avgFromInternal, AVG(x.fromBack) as avgFromBack' \
            ' FROM (' \
            '     SELECT i.readMoreSource, i.appInstallID, s.length, s.totalPages, s.fromSearch, s.fromRandom, s.fromInternal, s.fromBack,' \
            '         s.timestamp, ROUND(TIMEDIFF(NOW(), s.timestamp) / 600) as sessionTime' \
            '     FROM MobileWikiAppSessions s' \
            '     JOIN MobileWikiAppArticleSuggestions i' \
            '         ON i.appInstallID = s.appInstallID' \
            '     GROUP BY ROUND(TIMEDIFF(NOW(), s.timestamp) / 600)' \
            '     ORDER BY s.appInstallID, s.timestamp' \
            ' ) as x' \
            ' GROUP BY x.readMoreSource'
        df = pd.read_sql(sql, con=self.db)
        return self.set_read_more_source_label(df)

    def get_page_scroll_stats(self):
        return pd.read_sql('SELECT COUNT(*), AVG(maxPercentViewed), AVG(timeSpent), SUM(timeSpent) FROM MobileWikiAppPageScroll', con=self.db)

    def get_metric_stats(self):
        sql = "SELECT COUNT(*) as events FROM MobileWikiAppArticleSuggestions"
        self.cur.execute(sql)

        events = self.cur.fetchall()[0]['events']


        sql = "SELECT COUNT(DISTINCT appInstallID) as users FROM MobileWikiAppArticleSuggestions"
        self.cur.execute(sql)

        users = self.cur.fetchall()[0]['users']

        #print('Users collected: %i' % )


        df = pd.DataFrame.from_dict({
            '_metric': [
                'users',
                'suggestions'
            ],
            'count': [
                users,
                events
            ]
        })
        return df
