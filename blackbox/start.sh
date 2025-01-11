#!/bin/bash
#
docker run -d --name=blackboxexporter \
        -p 9115:9115 \
        -v $(pwd)/blackbox_config.yml:/etc/black_exporter/config.yml \
        --network monitoring_default \
        prom/blackbox-exporter:latest \
        --config.file=/etc/black_exporter/config.yml

