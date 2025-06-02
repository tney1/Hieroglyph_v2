#! /bin/bash
# NOTE: Work in Progress
export SUDO_ASKPASS="$HOME/.support"
SUDO="sudo --askpass"

set -e
log() {
    # Log with level to stderr
    local msg="$1"
    local level="${2:-INFO}"
    echo "[$level] $msg" 1>&2
}
assert_present() {
    # TODO: Test
    # Assert that all files provided in $@ are present
    for file in "$@"; do
        log "Checking for $file"
        if [ ! -f "$file" ]; then
            log "Missing $file" "ERROR"
            echo 1
        fi
    done
}
assert_loaded() {
    # TODO: Test
    # Assert that argument $1 docker image is loaded
    local image_name="$1"
    if [[ "$(docker images -q $image_name 2> /dev/null)" == "" ]]; then
        log "Missing image: $image_name" "ERROR"
        echo 1
    fi
}
assert_versions() {
    # TODO: Test
    # List of dependencies comma separated PROGRAM (>= VERSION), assert installed and version >= VERSION
    local packages="$1"
    log "Checking for packages: $packages" "DEBUG"
    if [ ! `${SUDO} apt-get -qq satisfy "$packages" 2>/dev/null` ]; then
        log "Dependency version error" "ERROR"
        echo 1
    fi
}
attempt_install() {
    # TODO: Test
    # List of dependencies space separated PROGRAM, attempt install
    local packages="$1"
    log "Attempting to install packages: $packages" "DEBUG"
    if [ ! `${SUDO} apt-get -qq -y install $packages 2>/dev/null` ]; then
        log "Dependency install error" "ERROR"
        echo 1
    fi
}
assert_pip_versions() {
    # TODO
    # Filename corresponding to requirements.txt file, assert installed and version >= VERSION
}
attempt_pip_install() {
    # TODO
    # Filename corresponding to requirements.txt file, attempt install
}

VERSION="${1:-$(cat VERSION)}"
log "Script Pad Version: $VERSION"

CONTENT_ZIP="script-pad_$VERSION.tar.gz"
IMAGE="svc-prod:online"
SCRIPTPAD_DIRECTORY='./script-pad'
SUBMITTER_SCRIPT="$SCRIPTPAD_DIRECTORY/submitter.py"
MODEL_ZIP="$SCRIPTPAD_DIRECTORY/models.tar.gz"
IMAGE_ZIP="$SCRIPTPAD_DIRECTORY/svc-prod_online.tar.gz"
DOCKER_COMPOSE="$SCRIPTPAD_DIRECTORY/docker-compose.yml"
SUBMITTER_SCRIPT_DEPENDENCIES="$SCRIPTPAD_DIRECTORY/requirements.submitter.txt"
SUBMITTER_VENV="$SCRIPTPAD_DIRECTORY/venv"

MIN_DOCKER_VERSION=20
MIN_DOCKER_COMPOSE_VERSION=1.25.0
MIN_PYTHON_VERSION=3.8.0
PYTHON_BINARY='python3'
DOCKER_PACKAGE='docker.io'
DOCKER_COMPOSE_PACKAGE='docker-compose'
DEPENDENCIES="$DOCKER_PACKAGE $DOCKER_COMPOSE_PACKAGE $PYTHON_BINARY"
DEPENDENCIES_VERSIONS="$DOCKER_PACKAGE (>= $MIN_DOCKER_VERSION), $DOCKER_COMPOSE_PACKAGE (>= $MIN_DOCKER_COMPOSE_VERSION), $PYTHON_BINARY (>= $MIN_PYTHON_VERSION)"

START_TIME=`date +%s`


###################################################################
log "Check general app dependencies: $DEPENDENCIES_VERSIONS"
if `! assert_versions "$DEPENDENCIES_VERSIONS"`; then
    attempt_install "$DEPENDENCIES"
fi
assert_versions "$DEPENDENCIES_VERSIONS"

###################################################################
log "Check submitter script dependencies in $SUBMITTER_SCRIPT_DEPENDENCIES -> `cat $SUBMITTER_SCRIPT_DEPENDENCIES`"
if `! assert_pip_versions "$SUBMITTER_SCRIPT_DEPENDENCIES"`; then
    attempt_pip_install "$SUBMITTER_SCRIPT_DEPENDENCIES"
fi
assert_pip_versions "$DEPENDENCIES"


###################################################################
log "Check if necessary files are present: $CONTENT_ZIP"
tar -xzvf $CONTENT_ZIP -C $SCRIPTPAD_DIRECTORY
assert_present $MODEL_ZIP $IMAGE_ZIP $DOCKER_COMPOSE $SUBMITTER_SCRIPT $SUBMITTER_SCRIPT_DEPENDENCIES


###################################################################
log "Load service container image: $IMAGE"
docker load -i "$IMAGE_ZIP"
assert_loaded "$IMAGE"

###################################################################
END_TIME=`date +%s`
RUNTIME=$((END_TIME-START_TIME))

log "Finished in $RUNTIME seconds, start with: ./app/scriptpad.sh"
