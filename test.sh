#!/bin/bash

# Basic citolytics install tests.

set -e

# no cache
docker-compose up

curl http://localhost/api/rest_v1/page/html/Main_Page \ | grep -q "MediaWiki has been successfully installed"

echo "Everything looks good."
exit 0
