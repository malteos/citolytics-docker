# Docker Container for Citolytics (WIP)

***WARNING:*** This container is still under development.

Containerized [MediaWiki](https://mediawiki.org) setup + [Citolytics](https://github.com/wikimedia/citolytics) demo.

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
sudo docker run -it mediawiki python /scripts/eventlogging/process_logs.py --db-host mysql --override
```

## Copy EventLogging data from container (run as cron)

```
sudo docker cp mediawiki:/var/log/nginx/events.log /srv/wikisim/events.log.$(date +%s)
```

## TODO

- Tests

## License

MIT
