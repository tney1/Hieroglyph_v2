#! /bin/bash
set -e
log() {
    local msg="$1"
    local level="${2:-INFO}"
    echo "[$level] $msg"
}

# SET THESE IF NECCESARY
REPACKAGE_MODELS="${1:-0}"
MODEL_DIR="${2:-models}"
GUI_DIR="${3:-app}"
IMAGE="${4:-svc-prod:online}"

VERSION=$(cat VERSION)

CONTENT_ZIP="script-pad_$VERSION.tar.gz"
DOCKER_COMPOSE='docker-compose.yml'
SUBMITTER_SCRIPT='scripts/submitter.py'
SUBMITTER_SCRIPT_DEPENDENCIES='requirements.submitter.txt'
GUI_SCRIPT_DEPENDENCIES="requirements.gui.txt"
EXAMPLES_DIR="assets/examples"

START_TIME=`date +%s`
###################################################################
MODEL_ZIP="$MODEL_DIR.tar.gz"

log "Grab the models from $MODEL_DIR and place into $MODEL_ZIP"
if [ "$REPACKAGE_MODELS" = "1" ]; then
    tar -czvf $MODEL_ZIP $MODEL_DIR
fi
###################################################################
EXAMPLES_ZIP="$(basename $EXAMPLES_DIR).tar.gz"

log "Grab the examples from $EXAMPLES_DIR and place into $EXAMPLES_ZIP"
tar -czvf $EXAMPLES_ZIP -C $EXAMPLES_DIR/ .


###################################################################
GUI_ZIP="$GUI_DIR.tar.gz"

log "Grab the GUI from $GUI_DIR and place into $GUI_ZIP"
tar -czvf $GUI_ZIP -C $GUI_DIR .

###################################################################
IMAGE_ZIP="$(echo $IMAGE | sed 's/:/_/g').tar.gz"

log "Saving service container image: $IMAGE to $IMAGE_ZIP"
docker-compose -f $DOCKER_COMPOSE build
docker save $IMAGE | gzip > $IMAGE_ZIP

###################################################################
log "Zipping all relevant content into $CONTENT_ZIP"
tar -czvf $CONTENT_ZIP $MODEL_ZIP $IMAGE_ZIP $DOCKER_COMPOSE $SUBMITTER_SCRIPT $SUBMITTER_SCRIPT_DEPENDENCIES 

###################################################################
END_TIME=`date +%s`
RUNTIME=$((END_TIME-START_TIME))

log "Finished in $RUNTIME seconds, content in $CONTENT_ZIP"
