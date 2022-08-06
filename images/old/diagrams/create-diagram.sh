#!/bin/bash

set -eu

if [ $# != 2 ]; then
  echo "Usage: sh create-diagram.sh <source path> <output file name>"
  exit 1
fi

SRC_PATH=$1
OUTPUT_NAME=$2
RESULT_FILE_PATH="./${OUTPUT_NAME}.png"

echo "executing ${SRC_PATH} ..."
python "${SRC_PATH}"

impbcopy "${RESULT_FILE_PATH}"
open "${RESULT_FILE_PATH}"
