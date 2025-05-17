#!/bin/bash

# Script for installing Nvdiai drivers in AlmaLinux 9.x version. 
# Generated with ChatGPT based on the my manual setup steps. Not tested. yet


set -e

ROLLBACK_FILE="/tmp/nvidia_driver_install_state"

echo "=== NVIDIA Driver Installation Script for AlmaLinux ==="

# Function to prompt user for Y/N
prompt_confirm() {
    while true; do
        read -rp "$1 [y/n]: " yn
        case $yn in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

# Check for Secure Boot
echo "Checking Secure Boot status..."
if mokutil --sb-state 2>/dev/null | grep -q "enabled"; then
    echo "Secure Boot is ENABLED. This may block unsigned kernel modules like NVIDIA drivers."
    echo "Disable Secure Boot from BIOS/UEFI before continuing."
    exit 1
else
    echo "Secure Boot is disabled. Proceeding..."
fi

# Step 1: Enable CRB and make cache
if prompt_confirm "Enable CRB and make cache?"; then
    sudo dnf config-manager --set-enabled crb
    sudo dnf makecache
fi

# Step 2: Install EPEL and update system
if prompt_confirm "Install EPEL and update system packages?"; then
    sudo dnf install -y epel-release
    sudo dnf upgrade -y
    sudo dnf update -y
fi

# Step 3: Add CUDA repo and update cache
if prompt_confirm "Add NVIDIA CUDA repository?"; then
    sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
    sudo dnf makecache
fi

# Step 4: Install NVIDIA driver
if prompt_confirm "Install NVIDIA driver module?"; then
    sudo dnf module install -y nvidia-driver
    echo "nvidia_driver_installed" > "$ROLLBACK_FILE"
fi

# Step 5: Install dev libraries
if prompt_confirm "Install OpenGL and dev libraries?"; then
    sudo dnf install -y freeglut-devel libX11-devel libXi-devel libXmu-devel make mesa-libGLU-devel freeimage-devel glfw-devel
fi

# Step 6: Validate installation
echo "Validating NVIDIA driver installation..."
if ! command -v nvidia-smi >/dev/null || ! nvidia-smi >/dev/null 2>&1; then
    echo "nvidia-smi failed. Would you like to blacklist nouveau and regenerate initramfs?"
    if prompt_confirm "Blacklist nouveau?"; then
        echo "blacklist nouveau" | sudo tee /etc/modprobe.d/blacklist-nouveau.conf
        echo 'omit_drivers+=" nouveau "' | sudo tee /etc/dracut.conf.d/blacklist-nouveau.conf
        sudo dracut --regenerate-all --force
        sudo depmod -a
        echo "nouveau_blacklisted" >> "$ROLLBACK_FILE"
        echo "Please reboot your system and re-run the script to continue."
        exit 0
    else
        echo "Aborting installation."
        exit 1
    fi
else
    echo "NVIDIA driver installed successfully."
fi

# Rollback section
rollback() {
    echo "Rolling back installation..."

    if grep -q "nouveau_blacklisted" "$ROLLBACK_FILE"; then
        echo "Removing nouveau blacklist..."
        sudo rm -f /etc/modprobe.d/blacklist-nouveau.conf
        sudo rm -f /etc/dracut.conf.d/blacklist-nouveau.conf
        sudo dracut --regenerate-all --force
        sudo depmod -a
    fi

    if grep -q "nvidia_driver_installed" "$ROLLBACK_FILE"; then
        echo "Removing NVIDIA drivers..."
        sudo dnf module remove -y nvidia-driver
    fi

    rm -f "$ROLLBACK_FILE"
    echo "Rollback completed."
}

# Ask for rollback
if prompt_confirm "Would you like to undo (rollback) this installation?"; then
    rollback
fi