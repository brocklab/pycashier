#!/usr/bin/env bash

# This script will remove some of the unnessary files from
# a conda environment to significantly reduce docker image size.

BASE_PATH=${1:-.pixi/envs/prod}
cd $BASE_PATH

find -name '*.a' -delete
find -name '__pycache__' -type d -exec rm -rf '{}' '+'
find lib/python3*/site-packages/ -name 'tests' -type d -exec rm -rf '{}' '+'
find lib/python3*/site-packages/ -name '*.pyx' -delete

rm -rf {conda-meta,include,man}
rm -rf lib/libpython3*.so.1.0
rm -rf lib/python3*/idlelib \
    lib/python3*/ensurepip \
    lib/libtk.* \
    lib/*tcl.* \
    lib/*sqlite3* \
    bin/x86_64-conda-linux-gnu-ld \
    bin/sqlite3 \
    bin/openssl \
    bin/nghttp* \
    share/terminfo
