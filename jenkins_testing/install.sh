#!/usr/bin/env bash
set -e

echo "Updating packages and installing dependencies..."
dnf update -y
dnf install -y zip unzip

echo "Installing SDKMAN..."
curl -s "https://get.sdkman.io" | bash

# Source SDKMAN script so we can use 'sdk' command in this shell
# Note: In a Docker build, the default user is 'root', so the home directory is /root
source "/root/.sdkman/bin/sdkman-init.sh"

echo "Installing Java 17 via SDKMAN..."
sdk install java 17.0.8-tem

echo "Installing Groovy via SDKMAN..."
sdk install groovy

echo "Installing Gradle via SDKMAN..."
sdk install gradle

echo "Setting up JAVA_HOME environment variable..."
JAVA_HOME=$(sdk home java 17.0.8-tem)
echo "export JAVA_HOME=$JAVA_HOME" >> /root/.bashrc
echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /root/.bashrc

echo "Installation completed successfully!"
