#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_NAME="trada-studio"
BUNDLE_NAME="trada-studio-linux-x86_64"

cd "$ROOT_DIR"

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install . pyinstaller

REFLEX_DIR=.reflex-home "$PYTHON_BIN" -m reflex compile

rm -rf build "dist/$APP_NAME" "dist/${BUNDLE_NAME}.tar.gz"

pyinstaller \
  --noconfirm \
  --clean \
  --onedir \
  --name "$APP_NAME" \
  --collect-all reflex \
  --add-data ".web:.web" \
  --add-data "assets:assets" \
  --add-data "storage:storage" \
  packaging/linux_launcher.py

tar -C dist -czf "dist/${BUNDLE_NAME}.tar.gz" "$APP_NAME"

echo "Linux bundle created at dist/${BUNDLE_NAME}.tar.gz"
