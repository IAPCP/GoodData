#!/bin/sh
BUILD_PATH=/workspace/build
ARCHIVE_PATH=/workspace/package
LD_ARCHIVE=${ARCHIVE_PATH}/ld
GCC_ARCHIVE=${ARCHIVE_PATH}/gcc
COMPILE_COMMANDS_DB=${ARCHIVE_PATH}/compile_commands.sqlite3
GCC_PARSER_HIJACK_DWARF4=1
GCC_PARSER_HIJACK_OPTIMIZATION=${2}
    
# Set noninteractive
export DEBIAN_FRONTEND=noninteractive

# Prepare environment variables
export ARCHIVE_PATH
export LD_ARCHIVE
export GCC_ARCHIVE
export COMPILE_COMMANDS_DB
export GCC_PARSER_HIJACK_DWARF4
export GCC_PARSER_HIJACK_OPTIMIZATION

{
    if [ $# -ne 2 ]; then
        echo "Usage: $0 <package_name> <optimization_level>"
        echo "optimization_level: 0, 1, 2, 3, s, g, fast"
        exit 1
    fi

    # Prepare directories

    mkdir -p ${BUILD_PATH}
    mkdir -p ${ARCHIVE_PATH}
    mkdir -p ${LD_ARCHIVE}
    mkdir -p ${GCC_ARCHIVE}

    # Start build process
    cd ${BUILD_PATH} && apt -y source --compile ${1}

    if [ $? -eq 0 ]; then
        touch ${ARCHIVE_PATH}/compile_succeed
        exit 0
    else
        exit 0
    fi
} 2>&1 > ${ARCHIVE_PATH}/compile.log