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

user_warning() {
    echo -e "${COLOR_CODE_YELLOW} [WARNING] $1${COLOR_CODE_DEFAULT}"
}

user_end_of_script() {
    echo -e "${COLOR_CODE_YELLOW} [~] $1${COLOR_CODE_DEFAULT}"
}

user_alert() {
    echo -e "${COLOR_CODE_RED} [ALERT] $1${COLOR_CODE_DEFAULT}"
}
# ------------------------------------------------------------

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

pull_docker() {

    image_tag="$1"

    if ! docker pull $image_tag &> /dev/null; then
        user_alert "$image_tag failed to be pulled. Check connectivity or manually pull via 'docker pull $image_tag'"
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$image_tag was pulled from Docker Registry. Continuing..."
    fi
}

build_docker() {

    image_tag="$1"
    dockerfile_name="$2"

    if ! docker build --network=host -t $image_tag -f $dockerfile_name . &> /dev/null; then
        user_alert "$image_tag failed to be built. Manually save via 'docker build --network=host -t $image_tag -f $dockerfile_name .'"
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$image_tag was built from Dockerfile. Continuing..."
    fi
}

# Arbritrary Variables
OUTPUT_BUNDLE_NAME="STAGE_THREE_BUNDLE"
OUTPUT_TAR="STAGE_THREE_BUNDLE.tar"
FRONTEND_APP_DIRECTORY="app"

# Project Variables
PROJ_TAG='shell:dependencies'
PROJ_IMG_TAR='shell_dependencies.tar.gz'

# Frontend Variables
FRONT_TAG='frontend:dependencies'
FRONT_IMG_TAR='frontend_dependencies.tar.gz'

# Mongo Variables
MONGO_TAG='mongo:latest'
MONGO_IMG_TAR='mongo_latest.tar.gz'

# Expected Files in STAGE_TWO_BUNDLE.tar Build Directory
REQ_FILE_NAME="requirements.txt"
DOCKERFILE_NAME="Dockerfile.online"
FRONTEND_DOCKERFILE="Dockerfile.frontend.online"
STAGE_TWO_NAME="stage-2-internet.sh"
STAGE_THREE_NAME="stage-3-offline.sh"
STAGE_FOUR_NAME="stage-4-deploy.sh"
FRONTEND_PKG="$FRONTEND_APP_DIRECTORY/package.json" # Package File for Frontend
FRONTEND_YARN="$FRONTEND_APP_DIRECTORY/yarn.lock" # Yarn Lock File for Frontend

cat << "EOF"

   \\\\   Welcome to Stage Two! The following script builds three docker
   c  oo  containers as Tarballs: 1) two bare containers of server/frontend
    | .U  project dependencies and 2) a MongoDB container. Users receive
   __=__  a Tarball to complete the build in their deployment environment.
   Vr 1.1

EOF

# Checks Files Present
user_standard "Step 1 - Verifying required files are present in this directory..."
assert_present $REQ_FILE_NAME $DOCKERFILE_NAME $STAGE_TWO_NAME $FRONTEND_PKG $FRONTEND_YARN

# Build Docker Image from Dockerfile.online
user_standard "Step 2 - Preparing server dependency container..."
build_docker $PROJ_TAG $DOCKERFILE_NAME

# Build Frontend Docker Image from Dockerfile.frontend.online
user_standard "Step 3 - Preparing frontend dependency container..."
build_docker $FRONT_TAG $FRONTEND_DOCKERFILE

# Pull MongoDB Backend Container from Docker Registry
user_standard "Step 4 - Pulling complete MongoDB backend container from Docker Registry..."
pull_docker $MONGO_TAG

# Save Docker Image to a Tarball on Disk
user_standard "Step 5 - Saving server dependency container to current directory as '$PROJ_IMG_TAR'..."
docker save $PROJ_TAG | gzip > $PROJ_IMG_TAR
user_success "Saved server container."

# Save Frontend Docker Image to a Tarball on Disk
user_standard "Step 6 - Saving frontend dependency container to current directory as '$FRONT_IMG_TAR'..."
docker save $FRONT_TAG | gzip > $FRONT_IMG_TAR
user_success "Saved frontend container.."

# Save Mongo DB Backend Container to a Tarball on Disk
user_standard "Step 7 - Saving MongoDB backend container to current directory as '$MONGO_IMG_TAR'..."
docker save $MONGO_TAG | gzip > $MONGO_IMG_TAR
user_success "Passed."

# Packaging into Stage Three Directory
user_standard "Step 8 - Bundling generated files for stage three of installation...."
mkdir -p $OUTPUT_BUNDLE_NAME # Creates Bundle Folder
mv $MONGO_IMG_TAR $OUTPUT_BUNDLE_NAME/$MONGO_IMG_TAR # Move Mongo Tarball to Bundle Folder
mv $PROJ_IMG_TAR $OUTPUT_BUNDLE_NAME/$PROJ_IMG_TAR # Move Server Tarball to Bundle Folder
mv $FRONT_IMG_TAR $OUTPUT_BUNDLE_NAME/$FRONT_IMG_TAR # Move Frontend Tarball to Bundle Folder
cp $STAGE_THREE_NAME $OUTPUT_BUNDLE_NAME/$STAGE_THREE_NAME # Copy Stage Three Install Script
cp $STAGE_FOUR_NAME $OUTPUT_BUNDLE_NAME/$STAGE_FOUR_NAME # Copy Stage Four Install Script
tar -cf $OUTPUT_TAR $OUTPUT_BUNDLE_NAME

# Completion
echo ""
user_success "Completed. All stage three files bundled into '$OUTPUT_TAR' in current directory."

user_standard "Move '$OUTPUT_TAR' to your deployment environment for the final step of the build. Goodbye!"
