#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Usage: $0 <package_name> <optimization_level>"
    echo "optimization_level: 0, 1, 2, 3, s, g, fast"
    exit 1
fi

# Prepare directories
BUILD_PATH=/root/build
ARCHIVE_PATH=/root/package
LD_ARCHIVE=/root/package/ld
GCC_ARCHIVE=/root/package/gcc
COMPILE_COMMANDS_DB=${ARCHIVE_PATH}/compile_commands.sqlite3
GCC_PARSER_HIJACK_DWARF4=1
GCC_PARSER_HIJACK_OPTIMIZATION=${2}

mkdir -p ${BUILD_PATH}

mkdir -p ${ARCHIVE_PATH}
mkdir -p ${LD_ARCHIVE}
mkdir -p ${GCC_ARCHIVE}

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
export ARCHIVE_PATH
export LD_ARCHIVE
export GCC_ARCHIVE
export COMPILE_COMMANDS_DB
export GCC_PARSER_HIJACK_DWARF4
export GCC_PARSER_HIJACK_OPTIMIZATION

# Start build process
cd ${BUILD_PATH} && apt -y source --compile ${1}

if [ $? -eq 0 ]; then
    touch ${ARCHIVE_PATH}/compile_succeed
    exit 0
else
    exit 1
fi
