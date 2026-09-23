#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

pick_python() {
  local candidate
  for candidate in \
    "/usr/local/opt/python@3.13/bin/python3.13" \
    "/opt/homebrew/opt/python@3.13/bin/python3.13" \
    "/usr/local/opt/python@3.12/bin/python3.12" \
    "/opt/homebrew/opt/python@3.12/bin/python3.12" \
    "$(command -v python3.13 || true)" \
    "$(command -v python3 || true)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      if "$candidate" -c "import tkinter" >/dev/null 2>&1; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON_BIN="$(pick_python || true)"

if [ -z "$PYTHON_BIN" ]; then
  echo "Error: no compatible Python with tkinter found."
  echo "Install Homebrew Python: brew install python@3.12"
  exit 1
fi

if ! command -v gcc >/dev/null 2>&1; then
  echo "Error: gcc is not installed or not in PATH."
  exit 1
fi

mkdir -p data

if command -v make >/dev/null 2>&1; then
  make build
else
  gcc -Wall -Wextra -std=c99 -o analyzer analyzer.c
fi

"$PYTHON_BIN" -m py_compile app.py
echo "Using Python: $PYTHON_BIN"
"$PYTHON_BIN" app.py
