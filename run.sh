#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_DIR/venv/bin/activate"
python "$PROJECT_DIR/fstasearch.py" "$@"
