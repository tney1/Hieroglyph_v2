#! /bin/bash
set -ex
echo "[+] Starting scriptpad, install package first"
python3 /opt/app/setup.py develop
python3 /opt/app/src/scriptpad/script_pad.py -l "chinese"
