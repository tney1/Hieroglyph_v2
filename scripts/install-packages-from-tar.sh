#! /bin/bash
set -ex
PYTHON_EX="${PYTHON_EX:-python3.11}"

TARFILE="${1:-./packages.tar.gz}"
TARGET_DIRECTORY="${2:-./packages/}"

if [[ -f "$TARFILE" ]]; then
	echo "[+] Unarchiving $TARFILE" 
	tar -xvf $TARFILE $TARGET_DIRECTORY
else
	echo "[!] ERROR no tarfile to extract packages from: [$TARFILE]"
	exit 1
fi

echo "[+] Installing packages"
$PYTHON_EX -m pip install --no-index --find-links ./$TARGET_DIRECTORY/ -r ./$TARGET_DIRECTORY/requirements.txt
