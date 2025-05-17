#!/bin/bash

if ! command -v ethtool &> /dev/null; then
    echo "ethtool is not installed. Please install it first."
    exit 1
fi

echo "Identifying Ethernet devices and gathering info..."

interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -v lo)

for iface in $interfaces; do
    if ethtool "$iface" &> /dev/null; then
        echo
        echo "=== Interface: $iface ===="
        ip -br addr show "$iface"
        echo "--- ethtool output ---"
        ethtool "$iface"
    fi
done
