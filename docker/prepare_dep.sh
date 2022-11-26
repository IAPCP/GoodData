#!/bin/sh

if [ $# -ne 1 ]; then
    echo "Usage: $0 <package_name>"
    exit 1
fi

# Set noninteractive
export DEBIAN_FRONTEND=noninteractive

# Update
apt -y update
apt -y upgrade

# Install build dependencies
apt -y build-dep ${1}

# Restore libstdc++ to self-compiled version
rm /usr/lib/x86_64-linux-gnu/libstdc++.so.6
ln -s /usr/lib64/libstdc++.so.6 /usr/lib/x86_64-linux-gnu/libstdc++.so.6