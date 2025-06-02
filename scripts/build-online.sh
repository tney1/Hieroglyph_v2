#! /bin/bash
# BUILDS IMAGE ONLINE SO IT CAN BE MOVED OFFLINE TO RUN
set -e
OUTPUT_IMAGE="${1:-../svc-online.tar.gz}"
echo "[+] Building online via docker compose [just builds the image with dependencies and saves it]"
docker build -t svc:online -f Dockerfile.online .
echo "[+] Saving image"
docker save svc:online | gzip > $OUTPUT_IMAGE
