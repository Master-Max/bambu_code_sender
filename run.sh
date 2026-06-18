#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/home/mx/xProject/bambu_code_sender"
VENV_ACTIVATE="${PROJECT_DIR}/venv/bin/activate"
SCRIPT="${PROJECT_DIR}/main.py"

source "${VENV_ACTIVATE}"

python3 "${SCRIPT}"
