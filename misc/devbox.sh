#!/bin/bash

BASE_IMAGE="ubuntu:22.04"
# TODO: get this as argument from user
CONTAINER_NAME="experiment"

# start or restore the container
start_container() {
    container_id=$(docker ps -a -q -f "name=$CONTAINER_NAME")
    
    if [ -n "$container_id" ]; then
        echo "Restoring container state..."
        docker start -ai "$CONTAINER_NAME"
    else
        echo "Creating a new container..."
        docker run -it --name "$CONTAINER_NAME" "$BASE_IMAGE"
    fi
}

save_container_state() {
    echo "Saving container state..."
    timestamp=$(date +"%Y%m%d%H%M%S")
    docker commit "$CONTAINER_NAME" "${CONTAINER_NAME}_backup_$timestamp" >/dev/null
    echo "Container state saved as: ${CONTAINER_NAME}_backup_$timestamp"
}

case "$1" in
    start)
        start_container
        ;;
    save)
        save_container_state
        ;;
    cleanup)
        echo "Cleaning up old backups..."
        docker images "${CONTAINER_NAME}_backup_*" -q | xargs docker rmi -f
        ;;
    *)
        echo "Usage: $0 {start|save|cleanup}"
        exit 1
        ;;
esac
