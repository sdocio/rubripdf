#!/usr/bin/env bash
# RubriPDF launcher for Linux and macOS.
set -e
cd "$(dirname "$0")"

# Local fallback virtual environment (override with e.g. VENV_DIR=env ./run.sh)
VENV_DIR="${VENV_DIR:-.venv}"

# 1) If a virtual environment is already active, use it as-is.
if [ -n "$VIRTUAL_ENV" ]; then
    exec python app.py
fi

# 2) Find a Python 3 interpreter (python3 on most systems, python as fallback).
PY=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1 &&
       "$cand" -c 'import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)' 2>/dev/null; then
        PY="$cand"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "Python 3 is required. Please install it from https://python.org" >&2
    exit 1
fi

# 3) Create the local virtual environment on first run.
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR…"
    if ! "$PY" -m venv "$VENV_DIR"; then
        echo "Could not create a virtual environment." >&2
        echo "On Debian/Ubuntu you may need:  sudo apt install python3-venv" >&2
        exit 1
    fi
    "$VENV_DIR/bin/pip" install -q -r requirements.txt
fi

exec "$VENV_DIR/bin/python" app.py
