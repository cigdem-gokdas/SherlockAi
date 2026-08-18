#!/bin/zsh
set -euo pipefail
cd "${0:A:h}/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install -q -e .
python -m sherlock_ai
