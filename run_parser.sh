#!/bin/bash
# Convenience script to run the QMDL parser with the virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please run: python3 -m venv venv && venv/bin/pip install -e qmdl-offline-parser/.[fastcrc]"
    exit 1
fi

"$VENV_PYTHON" -m scat.main "$@"
