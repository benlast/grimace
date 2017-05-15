#!/usr/bin/env bash

VERSION="$(python setup.py --grimace-version)"

docker build \
    -t grimace:${VERSION}-python2 \
    -f docker/python2.Dockerfile \
    .

docker run --rm \
    -v $(pwd):/grimace \
    grimace:${VERSION}-python2 \
    docker/run_tests.sh python2

docker build \
    -t grimace:${VERSION}-python3 \
    -f docker/python3.Dockerfile \
    .

docker run --rm \
    -v $(pwd):/grimace \
    grimace:${VERSION}-python3 \
    docker/run_tests.sh python3

