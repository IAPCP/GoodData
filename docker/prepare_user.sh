#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Usage: $0 <pid> <gid>"
    exit 1
fi

addgroup --gid ${2} build
adduser --disabled-password --gecos "" --uid ${1} --gid ${2} build

chown build:build /workspace/package