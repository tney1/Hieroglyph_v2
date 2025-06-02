#! /bin/bash
set -ex
echo "[+] Starting scriptpad"
docker-compose -f docker-compose.dev.yml up
