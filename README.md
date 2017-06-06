# Docker Container for Citolytics

Containerized [MediaWiki](https://mediawiki.org) setup + [Citolytics](https://github.com/wikimedia/citolytics) demo.

## Install

Run the following commands (as root) and afterwards the MediaWiki will be available at `http://localhost` (port 80):

```
git clone https://github.com/mschwarzer/citolytics-docker
cd citolytics-docker
docker-compose build
docker-compose up
```
