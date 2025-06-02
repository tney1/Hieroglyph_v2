#! /bin/bash

# Read the BUILD.md for clear instructions!
# This Stage 1 script builds a tarball which contains:
# 1) Dockerfile.online
# 2) requirements.txt
# 3) stage-2-internet.sh
# 4) stage-3-offline.sh

# Requirements:
# * Python 3.11

# Coloring and Style

COLOR_CODE_DEFAULT='\033[1;37m'
COLOR_CODE_GREEN='\033[1;32m'
COLOR_CODE_YELLOW='\033[1;33m'

user_standard() {
    echo -e "${COLOR_CODE_DEFAULT}[~] $1${COLOR_CODE_DEFAULT}"
}

user_success() {
    echo -e "${COLOR_CODE_GREEN}[+] $1${COLOR_CODE_DEFAULT}"
}

user_warning() {
    echo -e "${COLOR_CODE_YELLOW}[~] $1${COLOR_CODE_DEFAULT}"
}

# ------------------------------------------------------------

cat << "EOF"

   \\\\   The following script generates a tarball users transfer from an
   c  oo  OFFLINE build environment to an ONLINE build environment. Once
    | .U  generated, move the file across networks and run the shell script
   __=__  you will find included in the tarball. See BUILD.md for details!
   Vr 1.1

EOF

# Where All Resources Are Pulled- Ensure Locations Exists!
HIEROGLYPH_DIRECTORY="/home/$USER/hieroglyph"
BUILD_DIRECTORY="build"
FRONTEND_DIRECTORY="frontend"
FRONTEND_APP_DIRECTORY="app"

# Arbritrary Variables
REQ_FILE_NAME="requirements.txt" # Requirements File from Base Directory
DOCKERFILE_NAME="Dockerfile.online" # Dockerfile for Online Systems
FRONTEND_DOCKERFILE="Dockerfile.frontend.online" # Dockerfile for Frontend
STAGE_TWO_NAME="stage-2-internet.sh" # Installer for Online Systems
STAGE_THREE_NAME="stage-3-offline.sh" # Installer for Final Stage
FRONTEND_PKG="$FRONTEND_APP_DIRECTORY/package.json" # Package File for Frontend
FRONTEND_YARN="$FRONTEND_APP_DIRECTORY/yarn.lock" # Yarn Lock File for Frontend

# Files to Bundle
OUTPUT_NAME="STAGE_TWO_BUNDLE.tar" # What to Name the Archive

# Output Location
OUTPUT_LOCATION="$BUILD_DIRECTORY/$OUTPUT_NAME"

# Command Sequence
user_standard "Generating a Tarball ($OUTPUT_NAME) in ($HIEROGLYPH_DIRECTORY)"
user_warning "Running..."
cd $HIEROGLYPH_DIRECTORY

# Copies Requirements File from Base Directory to Build Directory
cp $REQ_FILE_NAME $BUILD_DIRECTORY/$REQ_FILE_NAME

# Creates a Tarball Named STAGE_TWO_BUNDLE.tar
## Creates App Dir with Package and Yarn Files
tar -cf $OUTPUT_NAME -C $FRONTEND_DIRECTORY $FRONTEND_PKG $FRONTEND_YARN
## Appends Build Files to Tarball
tar -rf $OUTPUT_NAME -C $BUILD_DIRECTORY $REQ_FILE_NAME $DOCKERFILE_NAME $FRONTEND_DOCKERFILE $STAGE_TWO_NAME $STAGE_THREE_NAME

# Clean-Up Requirements File from Build Directory
rm $BUILD_DIRECTORY/$REQ_FILE_NAME

user_success "Completed! File deposited in '$HIEROGLYPH_DIRECTORY/$OUTPUT_NAME'."
