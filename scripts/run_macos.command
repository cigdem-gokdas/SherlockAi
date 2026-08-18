#!/bin/zsh
set -euo pipefail
cd "${0:A:h}/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
export SHERLOCKAI_ROOT="$PWD"
python -m pip install -q .
python -m sherlock_ai
