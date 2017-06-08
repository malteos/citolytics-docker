#FROM richarvey/nginx-php-fpm
FROM webdevops/php-nginx:ubuntu-16.04

# git, curl already installed
# python3 missing (use py2 instead)
#
RUN set -x; \
  apt-get update \
  && apt-get install -y less vim python-pip libmysqlclient-dev

ENV WEBROOT /var/www/
ENV MEDIAWIKI_DIR /var/www/public/mediawiki

# REL1_29 REL1_28
ENV MEDIAWIKI_BRANCH master

WORKDIR /var/www/public/mediawiki

# Copy Nginx & MediaWiki config
#COPY ./conf/nginx/nginx-site.conf /etc/nginx/sites-enabled/default
COPY ./conf/nginx/vhost.conf /opt/docker/etc/nginx/vhost.conf

COPY ./conf/mediawiki/CustomSettings.php $WEBROOT/CustomSettings.php

COPY get-data.sh /get-data.sh

# Restart nginx
# CMD supervisorctl restart nginx

# ADD elasticsearch.yml /usr/share/elasticsearch/config/
# USER root
# RUN chown elasticsearch:elasticsearch config/elasticsearch.yml
# USER elasticsearch

COPY docker-entrypoint.sh /entrypoint.sh
#ENTRYPOINT ["/entrypoint.sh"]
CMD /entrypoint.sh

CMD ["supervisord"]
