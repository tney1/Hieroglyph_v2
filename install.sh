#!/bin/bash

CURRENT_HOME=/home/$USER/

export SUDO_ASKPASS="$HOME/.support"
SUDO="sudo --askpass"

START_TIME=`date +%s`

# Name and Version Information
SC_NAME="HIEROGLYPH"
SC_VERSION="1.0"

# Logging
COLOR_CODE_DEFAULT='\033[1;37m'
COLOR_CODE_GREEN='\033[1;32m'
COLOR_CODE_YELLOW='\033[1;33m'
COLOR_CODE_RED='\033[1;31m'

RUSSIAN_CONTAINER="svc-rus"
CHINESE_CONTAINER="svc-chi"

# Name of Master TAR File Containing All Repository Resources
MASTER_TAR="hieroglyph_v1.0.0.tar.gz"

# Where All Resources Are Sent - Ensure Location Exists!
HIEROGLYPH_DIRECTORY='/usr/share/hieroglyph'

# Required Repository Resources and Files
IMAGE="svc-prod:online"
MODEL_ZIP="$HIEROGLYPH_DIRECTORY/models.tar.gz"
IMAGE_ZIP="$HIEROGLYPH_DIRECTORY/svc-prod_online.tar.gz"
GUI_ZIP="$HIEROGLYPH_DIRECTORY/app.tar.gz"
DOCKER_COMPOSE="$HIEROGLYPH_DIRECTORY/docker-compose.yml"
SUBMITTER_SCRIPT="$HIEROGLYPH_DIRECTORY/scripts/submitter.py"
SUBMITTER_SCRIPT_DEPENDENCIES="$HIEROGLYPH_DIRECTORY/requirements.submitter.txt"
GUI_SCRIPT_DEPENDENCIES="$HIEROGLYPH_DIRECTORY/requirements.gui.txt"

# GUI Application Resources
APP_DIRECTORY="$HIEROGLYPH_DIRECTORY"

LOCAL_ICON="$APP_DIRECTORY/hieroglyph-icon.png"
LOCAL_EXEC_SCRIPT="$APP_DIRECTORY/hieroglyph.sh"
LOCAL_DESKTOP_SHORTCUT="$APP_DIRECTORY/hieroglyph.desktop"
LOCAL_SUBMITTER="$SUBMITTER_SCRIPT"

ICON_DEST="$HIEROGLYPH_DIRECTORY/hieroglyph-icon.png"
EXEC_DEST="/usr/bin/hieroglyph"
DESKTOP_DEST="/usr/share/applications/hieroglyph.desktop"
SUBMITTER_DEST="$HIEROGLYPH_DIRECTORY/submitter.py"

# Examples
EXAMPLES_ZIP="$HIEROGLYPH_DIRECTORY/examples.tar.gz"
EXAMPLES_DEST="$CURRENT_HOME/Desktop/examples"

# Packages and Versions
MIN_DOCKER_VERSION=20
MIN_DOCKER_COMPOSE_VERSION=1.25.0
MIN_PYTHON_VERSION=3.11
PYTHON_PACKAGE='python3'
DOCKER_PACKAGE='docker.io'
DOCKER_COMPOSE_PACKAGE='docker-compose'
DEPENDENCIES="$DOCKER_PACKAGE $DOCKER_COMPOSE_PACKAGE $PYTHON_PACKAGE"
DEPENDENCIES_VERSIONS="$DOCKER_PACKAGE (>= $MIN_DOCKER_VERSION), $DOCKER_COMPOSE_PACKAGE (>= $MIN_DOCKER_COMPOSE_VERSION), $PYTHON_PACKAGE (>= $MIN_PYTHON_VERSION)"

VENV="/home/$USER/.virtualenvs/hieroglyph"
PIP_B="$VENV/bin/pip"
PYTHON_B="$VENV/bin/python"

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

create_virtual_environment() {
    rm -rf $VENV || true
    "python$MIN_PYTHON_VERSION" -m venv $VENV
}

check_dir() {

    passed_dir="$1"

    [ ! -d "$passed_dir" ] && mkdir -p $passed_dir

}

check_apt_pkg() {

    package_to_check="$1"

    if ! dpkg -s $package_to_check &> /dev/null; then
        user_alert "$package_to_check is not installed. Please install and try again."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$package_to_check was found. Continuing..."
    fi
}

check_pip_pkg() {

    wheel_to_check="$1"

    if ! $PIP_B show $wheel_to_check &> /dev/null; then
        user_alert "python '$wheel_to_check' library is not installed. Please install and try again."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "python '$wheel_to_check' library was found. Continuing..."
    fi
}

install_pip_req_file() {

    requirements_file="$1"

    if ! $PIP_B install -r $requirements_file &> /dev/null; then
        user_alert "Failed to install requirements file '$requirements_file'."
    else
        user_success "Requirements file '$requirements_file' was installed. Continuing..."
    fi
}

force_move_files() {

    local_file="$1"
    dest_file="$2"
    # This can fail, if the file doesn't exist that is okay
    rm -f $dest_file || true
    
    if ! sudo cp -f $local_file $dest_file &> /dev/null; then
        user_alert "Failed to move '$local_file' to '$dest_file'."
    else
        user_success "Successfully moved '$local_file' to '$dest_file'. Continuing..."
    fi
}

load_docker() {

    base_image="$1"

    if ! sudo docker load --input $base_image &> /dev/null; then
        user_alert "$base_image failed to be installed. Attempt manual install via 'docker load --input <path_to_img>'"
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$base_image was installed. Continuing..."
    fi
}

unpack_tar() {

    tar_file="$1"
    tgt_dir="$2"

    if ! sudo tar -xzvf $tar_file -C $tgt_dir  &> /dev/null; then
        user_alert "$tar_file failed to be unpacked. Verify integrity of file."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$tar_file was unpacked. Continuing..."
    fi
}

start_api() {

    compose_file="$1"

    if ! sudo docker-compose -f $compose_file up -d  &> /dev/null; then
        user_alert "API failed to start. Verify integrity of $compose_file."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "API initiated and running. Continuing..."
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

assert_loaded() {
    image_name="$1"
    if [[ "$(sudo docker images -q $image_name 2> /dev/null)" == "" ]]; then
        user_alert "The docker image '$image_name' appears to be missing."
        user_alert "Exiting setup... Remediate displayed errors!"
    fi
}

check_docker_port() {
    container_name="$1"
    container_alias="$2"

    container_id=$(sudo docker ps --filter "name=$container_name" --format "{{.ID}}")
    if [ -z "$container_id" ]; then
        user_alert "$container_alias container does not exist. Check 'docker ps' to verify the container is running."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    fi

    port_number=$(sudo docker port "$container_id" | head -n 1)

    if [ -z "$port_number" ]; then
        user_alert "Could not identify port for $container_id. Check 'docker ps' to verify the container is running."
        user_alert "Exiting setup... Remediate displayed errors!"
        exit 1
    else
        user_success "$container_alias container (ID: $container_id) is running at $port_number"
    fi
}

cat << "EOF"

   \\\\
   c  oo
    | .U  We'll see what we can do
   __=__                        ,,,   
  |.  __|___                    oo ; 
  ||_/  /  /                    U= _  0
  \_/__/__E   o                 /   | |
   (___ ||    |~~~~~~~~~~~~~~~~'----'~|
   I---|||    |-----------------------|
   I   |||    |  Scriptpad v1.0 Setup |
   ^   '--''  ^                       ^

EOF

user_standard "Initializing $SC_NAME $SC_VERSION installation..."

# Step 1 - Check APT Packages Exist
user_standard "Checking SYSTEM package requirements..."
check_apt_pkg "docker.io"
check_apt_pkg "docker-compose"
check_apt_pkg "python$MIN_PYTHON_VERSION"
check_apt_pkg "python3-pip"

# Step 3 - Check if Necessary Files Are Present:
user_standard "Verifying required repository resources are present..."
check_dir $HIEROGLYPH_DIRECTORY
unpack_tar $MASTER_TAR $HIEROGLYPH_DIRECTORY
assert_present $MODEL_ZIP $IMAGE_ZIP $DOCKER_COMPOSE $SUBMITTER_SCRIPT $SUBMITTER_SCRIPT_DEPENDENCIES $EXAMPLES_ZIP

# Step 2 - Check Submitter Script Dependencies and create virtual environment
user_standard "Checking PYTHON package requirements..."
create_virtual_environment
install_pip_req_file $SUBMITTER_SCRIPT_DEPENDENCIES
check_pip_pkg "pdf2image"
check_pip_pkg "requests"

# Step 2a - Check GUI Script Dependencies
install_pip_req_file $GUI_SCRIPT_DEPENDENCIES
check_pip_pkg "PyQt5"

# Step 3a - Unpacking
user_standard "Unpacking all bundled files in $MASTER_TAR"
unpack_tar $GUI_ZIP $HIEROGLYPH_DIRECTORY
unpack_tar $MODEL_ZIP $HIEROGLYPH_DIRECTORY

# Step 4 - Load Base Image
user_standard "Starting installation of $SC_NAME $SC_VERSION Docker image..."
load_docker $IMAGE_ZIP
assert_loaded $IMAGE

# Step 5 - Start API
user_standard "Initiating $SC_NAME $SC_VERSION API..."
start_api $DOCKER_COMPOSE

# Step 6 - Check Running Ports and Display Locations
user_standard "Fetching network information for initiated $SC_NAME containers..."
check_docker_port $RUSSIAN_CONTAINER "Russian"
check_docker_port $CHINESE_CONTAINER "Chinese"

# Step 7 - GUI Resources
user_standard "Preparing resources for Scriptpad GUI..."
force_move_files $LOCAL_ICON $ICON_DEST
force_move_files $LOCAL_EXEC_SCRIPT $EXEC_DEST
force_move_files $LOCAL_DESKTOP_SHORTCUT $DESKTOP_DEST
force_move_files $LOCAL_SUBMITTER $SUBMITTER_DEST

# Step 8 - Place Examples on Desktop
user_standard "Placing examples in Desktop folder"
check_dir $EXAMPLES_DEST
unpack_tar $EXAMPLES_ZIP $EXAMPLES_DEST

# End of Installation Script
END_TIME=`date +%s`
RUNTIME=$((END_TIME-START_TIME))
user_end_of_script "$SC_NAME $SC_VERSION installation complete. Finished in $RUNTIME second(s)."
# user_end_of_script "Execute './app/hieroglyph.sh' to initiate."
