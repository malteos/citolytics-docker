FROM richarvey/nginx-php-fpm

# git, curl already installed

ENV WEBROOT /var/www/
ENV MEDIAWIKI_DIR /var/www/public/mediawiki

# REL1_29 REL1_28
ENV MEDIAWIKI_BRANCH master

WORKDIR /var/www/public/mediawiki

# Copy Nginx & MediaWiki config
COPY ./conf/nginx/nginx-site.conf /etc/nginx/sites-enabled/default
COPY ./conf/mediawiki/CustomSettings.php $WEBROOT/CustomSettings.php

#COPY ./mediawiki /var/www/public/mediawiki

# ADD elasticsearch.yml /usr/share/elasticsearch/config/
# USER root
# RUN chown elasticsearch:elasticsearch config/elasticsearch.yml
# USER elasticsearch

COPY docker-entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
