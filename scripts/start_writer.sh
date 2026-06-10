#!/bin/sh
cd /volume2/docker/tesvor-map || exit 1

export TESVOR_MQTT_HOST="${TESVOR_MQTT_HOST:-192.168.178.56}"
export TESVOR_MQTT_PORT="${TESVOR_MQTT_PORT:-1883}"
export TESVOR_MAP_DIR="${TESVOR_MAP_DIR:-/volume2/docker/tesvor-map}"

/usr/bin/python3 /volume2/docker/tesvor-map/tesvor_map_writer.py >> /volume2/docker/tesvor-map/writer.log 2>&1
