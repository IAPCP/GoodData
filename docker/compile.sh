#!/bin/sh

if [ $# -ne 3 ]; then
    echo "Usage: $0 <package_name> <uid> <gid>"
    exit 1
fi

package_name=${1}
uid=${2}
gid=${3}

export DEBIAN_FRONTEND=noninteractive

export SAVE_PATH=${SAVE_PATH:-/save}

export ARCHIVE_PATH=${ARCHIVE_PATH:-/workspace/package}
export BUILD_PATH=${BUILD_PATH:-/workspace/build}
export LD_ARCHIVE=${ARCHIVE_PATH}/ld
export GCC_ARCHIVE=${ARCHIVE_PATH}/gcc
export COMPILE_COMMANDS_DB=${ARCHIVE_PATH}/compile_commands.sqlite3
export GCC_PARSER_HIJACK_DWARF4=${GCC_PARSER_HIJACK_DWARF4:-1}
export GCC_PARSER_HIJACK_OPTIMIZATION=${GCC_PARSER_HIJACK_OPTIMIZATION:-0}

# Prepare user with same uid and gid as host
addgroup --gid ${gid} build
adduser --disabled-password --gecos "" --uid ${uid} --gid ${gid} build

# Prepare directories
mkdir -p ${BUILD_PATH}
mkdir -p ${ARCHIVE_PATH}
mkdir -p ${LD_ARCHIVE}
mkdir -p ${GCC_ARCHIVE}

# Change ownership of directories
chown -R build:build ${BUILD_PATH}
chown -R build:build ${ARCHIVE_PATH}
chown -R build:build ${SAVE_PATH}

# Install build dependencies
apt -y build-dep ${package_name}

# Restore libstdc++ to self-compiled version, as build-dep may change
rm /usr/lib/x86_64-linux-gnu/libstdc++.so.6
ln -s /usr/lib64/libstdc++.so.6 /usr/lib/x86_64-linux-gnu/libstdc++.so.6

# Prepare compile.log
touch ${SAVE_PATH}/compile.log
chown build:build ${SAVE_PATH}/compile.log    

{
    # Start build process
    su build -c "cd ${BUILD_PATH} && apt -y source --compile ${1}"

    if [ $? -eq 0 ]; then
        compile_succeed=1
    fi

    # Save build artifacts to SAVE_PATH
    if [ ${SAVE_PATH} != ${ARCHIVE_PATH} ]; then
        su build -c "cp -r ${ARCHIVE_PATH}/* ${SAVE_PATH}"
    fi

    if [ ${compile_succeed:=0} -eq 1 ]; then
        su build -c "touch ${SAVE_PATH}/compile_succeed"
    fi
} 2>&1 > ${SAVE_PATH}/compile.log