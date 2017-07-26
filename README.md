# Docker Container for Citolytics (WIP)

Containerized [MediaWiki](https://mediawiki.org) setup + [Citolytics](https://github.com/wikimedia/citolytics) demo. ***WARNING:*** This container is still under development.

## Requirements

- Install [Docker](https://docs.docker.com/engine/installation/) (docker + docker-engine) and [Docker Compose](https://docs.docker.com/compose/install/) (docker-compose)

## Install

Run the following commands (as root) and afterwards the MediaWiki will be available at `http://localhost` (port 80):

```
git clone https://github.com/mschwarzer/citolytics-docker.git
cd citolytics-docker
mkdir -p data/es; chmod 777 data/es
sudo docker-compose up
```

## Download and import Wikipedia and Citolytics data

```
docker run -it mediawiki /scripts/get-data.sh
```

## Import EventLogging data

This following command runs the EventLogging parser script in the MediaWiki container and sends the date to the MySQL container.
```
docker run -it mediawiki /eventlogging/process_logs.py --db-host mysql
```

## TODO

- Tests

## License

MIT
