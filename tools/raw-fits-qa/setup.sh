#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
test -x .venv/bin/python || "${PYTHON:-python3}" -m venv --copies .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
