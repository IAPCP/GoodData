#!/bin/sh

# Prepare directories
BUILD_PATH=/root/build
DB_PATH=/root/package
ARCHIVE_PATH=/root/package/archive
mkdir -p ${DB_PATH}
mkdir -p ${ARCHIVE_PATH}
mkdir -p ${BUILD_PATH}

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

# Prepare environment variables
export COMPILE_COMMANDS_DB=${DB_PATH}/compile_commands.db
export PROJ_ROOT=${BUILD_PATH}
export LD_ARCHIVE=${ARCHIVE_PATH}

# Start build process
cd ${PROJ_ROOT} && apt -y source --compile ${1}
