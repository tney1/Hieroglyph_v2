#! /bin/bash
set -e
echo "[+] Starting hieroglyph, install package first"
python /opt/app/setup.py develop
python /opt/app/src/hieroglyph/main.py
