#! /bin/bash

# Coloring and Style

COLOR_CODE_DEFAULT='\033[1;37m'
COLOR_CODE_GREEN='\033[1;32m'
COLOR_CODE_YELLOW='\033[1;33m'

user_standard() {
    echo -e "${COLOR_CODE_DEFAULT} [!] $1${COLOR_CODE_DEFAULT}"
}

user_success() {
    echo -e "${COLOR_CODE_GREEN} [SUCCESS] $1${COLOR_CODE_DEFAULT}"
}

user_alert() {
    echo -e "${COLOR_CODE_RED} [ALERT] $1${COLOR_CODE_DEFAULT}"
}
# ------------------------------------------------------------

unpack_tar() {

    tar_file="$1"

    if ! tar -xvf $tar_file  &> /dev/null; then
        user_alert "$tar_file failed to be unpacked. Verify integrity of file."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$tar_file was unpacked. Continuing..."
    fi
}

assert_present() {
    for file in "$@"; do
        if [ ! -f "$file" ]; then
            user_alert "Missing '$file'. Verify the repository contains the resource."
            user_alert "Exiting setup... Remediate displayed errors!"
            exit 1
        else
            user_success "Found '$file'. Continuing..."
        fi
    done
}

load_docker() {

    base_image="$1"

    if ! docker load --input $base_image &> /dev/null; then
        user_alert "$base_image failed to be installed. Attempt manual install via 'docker load --input <path_to_img>'"
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$base_image was installed. Continuing..."
    fi
}





# Compose File and Version
COMPOSE_FILE="docker-compose.yml"
VERS="v1.4"

cat << "EOF"

   \\\\   Welcome to Stage Four! This final script unpacks and loads the
   c  oo  Shippable tarball (containing all containers for the project). 
    | .U  To run, place HIEROGLYPH_BUNDLE_$VERS.tar on the target system.
   __=__  
   Vr 1.1

EOF


# Bundle to Ship
SHIP_BUNDLE_NAME="HIEROGLYPH_BUNDLE_$VERS"
SHIP_TAR="HIEROGLYPH_BUNDLE_$VERS.tar"

# Compose file
COMPOSE_FILE="docker-compose.yml"

# Hieroglyph Variables
HIERO_TAG='hieroglyph-server:latest'
HIERO_IMG_TAR='hieroglyph_server_latest.tar.gz'

# Frontend Variables
FRONT_TAG='hieroglyph-frontend:latest'
FRONT_IMG_TAR='hieroglyph_frontend_latest.tar.gz'

# Database Variables
MONGO_TAG='mongo:latest'
MONGO_IMG_TAR='mongo_latest.tar.gz'

# Models
MODELS_DIR='models'
MODELS_TAR='models.tar'


# Unpack Stage Four Bundle
user_standard "Checking current directory for Stage Four Bundle..."
assert_present $SHIP_TAR

user_standard "Preparing to unpack Stage Four Bundle..."
unpack_tar $SHIP_TAR

user_standard "Checking unpacked bundle for requisite files..."
assert_present "$HIERO_IMG_TAR" # Server
assert_present "$MONGO_IMG_TAR" # DB
assert_present "$FRONT_IMG_TAR" # Frontend
assert_present "$MODELS_TAR" # Models
assert_present "$COMPOSE_FILE" # Docker compose


user_standard "Unpacking models directory..."
unpack_tar "$MODELS_TAR"

# Load Image
# Runs: docker load --input HIEROGLYPH_BUNDLE_$VERS/hieroglyph_frontend_latest.tar.gz
user_standard "Loading Server docker container..."
load_docker "$HIERO_IMG_TAR"

user_standard "Loading Frontend docker container..."
load_docker "$FRONT_IMG_TAR"

user_standard "Loading Database docker container..."
load_docker "$MONGO_IMG_TAR"


user_success "Completed. Run 'docker-compose up' to start services."
