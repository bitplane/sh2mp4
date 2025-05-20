#!/usr/bin/env bash
set -euo pipefail

W=1280
H=720
OUT=output.mp4
SCRIPT_PATH="$(realpath ./run.sh)"
LAUNCH_SCRIPT="./launch.sh"

TMPDIR="$(mktemp -d -t recordenv.XXXXXXXX)"
FAKE_HOME="$TMPDIR/home"
RUNTIME_DIR="$TMPDIR/runtime"
CONFIG_DIR="$TMPDIR/config"
DATA_DIR="$TMPDIR/data"

mkdir -p "$FAKE_HOME" "$RUNTIME_DIR" "$CONFIG_DIR" "$DATA_DIR"
chmod 700 "$FAKE_HOME" "$RUNTIME_DIR"

cleanup() {
  echo "Cleaning up..."
  pkill -f "Xvfb :99" 2>/dev/null || true
  rm -rf "$TMPDIR"
}
trap cleanup EXIT INT TERM

env -i \
  HOME="$FAKE_HOME" \
  PATH="$PATH" \
  DISPLAY=:99 \
  XDG_RUNTIME_DIR="$RUNTIME_DIR" \
  XDG_CONFIG_HOME="$CONFIG_DIR" \
  XDG_DATA_HOME="$DATA_DIR" \
  W="$W" H="$H" OUT="$OUT" SCRIPT_PATH="$SCRIPT_PATH" \
  bash "$LAUNCH_SCRIPT"
