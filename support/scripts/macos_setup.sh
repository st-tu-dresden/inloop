#!/usr/bin/env bash
if ! command -v brew >/dev/null; then
    echo 'I cannot find `brew`. Please install Homebrew from https://brew.sh/.' 2>&1
    exit 1
fi

brew install redis python3 node && brew services start redis

if [[ $? != 0 ]]; then
    echo 'Setup failed.' 2>&1
    exit 1
fi

if ! command -v docker >/dev/null; then
    echo 'I cannot find `docker`. Please install Docker for Mac' 2>&1
    echo 'from https://www.docker.com/docker-mac.' 2>&1
    exit 1
fi
