#!/bin/bash

# Iterate over each item in the current directory
for dir in */ ; do
    # Check if the directory is a Git repository
    if [ -d "$dir/.git" ]; then
        echo "Pulling in $dir"
        # Go into the directory
        cd "$dir"
        # Pull from the Git repository
        git pull
        # Go back to the parent directory
        cd ..
    else
        echo "$dir is not a Git repository"
    fi
done
