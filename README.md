# Docker Container for Citolytics

Containerized [MediaWiki](https://mediawiki.org) setup + [Citolytics](https://github.com/wikimedia/citolytics) demo.

## Requirements

- Install [Docker](https://docs.docker.com/engine/installation/) (docker + docker-engine) and [Docker Compose](https://docs.docker.com/compose/install/) (docker-compose)

## Install

Run the following commands (as root) and afterwards the MediaWiki will be available at `http://localhost` (port 80):

```
git clone https://github.com/mschwarzer/citolytics-docker
cd citolytics-docker
mkdir es_data
chmod 777 es_data
sudo docker-compose up
```

## TODO

- Tests
- Import CirrusSearch/Citolytics data
- EventLogging parser
