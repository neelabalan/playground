#!/bin/bash

PASSWORD=${1:-"admin"}
ROUNDS=${2:-10}

if command -v htpasswd >/dev/null 2>&1; then
    HASH=$(htpasswd -bnBC $ROUNDS admin "$PASSWORD" | cut -d: -f2)
    
    # convert $2y$ to $2a$ for Jenkins compatibility
    JENKINS_HASH=$(echo "$HASH" | sed 's/^\$2y\$/\$2a\$/')
    
    echo "#jbcrypt:${JENKINS_HASH}"
else
    echo "error: htpasswd not found. Please install Apache httpd tools or use the Python version."
    exit 1
fi

# python version
# import bcrypt
# # Force $2a$ format by manipulating the salt (Jenkins compatibility)
# salt = bcrypt.gensalt(rounds=10, prefix=b'2a')
# hashed = bcrypt.hashpw('admin'.encode('utf-8'), salt).decode('utf-8')
# print(f'#jbcrypt:{hashed}')
