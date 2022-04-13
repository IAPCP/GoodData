#!/bin/sh
mkdir -p /root/package/build
mkdir -p /root/package/archive
export DEBIAN_FRONTEND=noninteractiva

# Update
apt -y update
apt -y upgrade

# Install build dependencies
apt -y build-dep ${1}

# Restore libstdc++ to self-compiled version
rm /usr/lib/x86_64-linux-gnu/libstdc++.so.6
ln -s /usr/lib64/libstdc++.so.6.0.29 /usr/lib/x86_64-linux-gnu/libstdc++.so.6

# Prepare environment variables
export COMPILE_COMMANDS_DB=/root/package/compile_commands.db
export PROJ_ROOT=/root/package/build
export ARCHIVE=/root/package/archive

# Start build process
cd /root/package/build && apt -y source --compile ${1}