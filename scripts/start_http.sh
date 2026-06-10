#!/bin/sh
cd /volume2/docker/tesvor-map || exit 1
/usr/bin/python3 -m http.server 8095 >> /volume2/docker/tesvor-map/http.log 2>&1
