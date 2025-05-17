#!/bin/bash

# Generated with ChatGPT 
# Not tested!

confirm() {
    local prompt="$1"
    local varname="$2"
    local response
    read -r -p "$prompt [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY])
            eval "$varname=true"
            ;;
        *)
            eval "$varname=false"
            ;;
    esac
}

echo "Docker Cache Cleaner Script"
echo "---------------------------"

confirm "1. Show current Docker disk usage?" do_df
confirm "2. Remove all stopped containers (docker container prune)?" do_prune_containers
confirm "3. Stop all running containers and remove all containers?" do_remove_all_containers
confirm "4. Remove dangling images only (docker image prune)?" do_dangling_images
confirm "5. Remove all unused images (docker image prune -a)?" do_all_images
confirm "6. Remove anonymous unused volumes (docker volume prune)?" do_anon_volumes
confirm "7. Remove all unused volumes including named volumes (docker volume prune -a)?" do_all_volumes
confirm "8. Remove Docker build cache (docker buildx prune)?" do_build_cache
confirm "9. Remove unused Docker networks (docker network prune)?" do_networks
confirm "10. Remove all unused Docker artifacts (docker system prune)?" do_system_prune
confirm "11. Remove all unused Docker artifacts including volumes (docker system prune --volumes -a)?" do_full_system_prune

echo
echo "Executing selected Docker cleanup operations..."
echo "-----------------------------------------------"

if $do_df; then
    docker system df
    echo
fi

if $do_prune_containers; then
    docker container prune -f
    echo
fi

if $do_remove_all_containers; then
    running_containers=$(docker ps -q)
    if [ -n "$running_containers" ]; then
        echo "Stopping running containers..."
        docker stop $running_containers
    else
        echo "No running containers to stop."
    fi
    echo "Removing all containers..."
    docker rm $(docker ps -a -q)
    echo
fi

if $do_dangling_images; then
    docker image prune -f
    echo
fi

if $do_all_images; then
    docker image prune -a -f
    echo
fi

if $do_anon_volumes; then
    docker volume prune -f
    echo
fi

if $do_all_volumes; then
    docker volume prune -a -f
    echo
fi

if $do_build_cache; then
    docker buildx prune -f
    echo
fi

if $do_networks; then
    docker network prune -f
    echo
fi

if $do_system_prune; then
    docker system prune -f
    echo
fi

if $do_full_system_prune; then
    docker system prune --volumes -a -f
    echo
fi

echo "Docker cache cleanup script finished."