#! /bin/bash
set -ex
PYTHON_EX=python3.11

# This argument is the tar.gz file from the flash drive, presuming that it isnt already in the current working directory
if [[ ! -z "$1" ]]; then
	echo "[+] Copying packages tar.gz file: $1"
	cp $1 .
fi

if [[ ! -d "./env/" ]]; then
	$PYTHON_EX -m venv env
fi

echo "[+] Removing old wheel packages"
rm -rf packages/

if [[ -f ./packages.tar.gz ]]; then
	echo "[+] Unarchiving packages.tar.gz" 
	tar -xvf packages.tar.gz
else
	echo "[!] ERROR no wheel packages to untar"
	exit 1
fi

echo "[+] Installing wheel packages"
./env/bin/python -m pip install --no-index --find-links ./packages/ -r ./packages/requirements.txt
./env/bin/python setup.py develop
