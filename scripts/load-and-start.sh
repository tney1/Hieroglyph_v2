#! /bin/bash

set -e

BASE_IMAGE="$1"
echo "[+] Loading base image from file: [$BASE_IMAGE]"
docker load --input $BASE_IMAGE
echo "[+] Starting docker services"
docker-compose -f docker-compose.yml up --build
