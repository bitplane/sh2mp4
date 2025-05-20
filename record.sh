#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
COMMAND="${1:-asciinema play /home/gaz/Videos/asciinema/faster.cast}"
OUT="${2:-output.mp4}"
COLS="${3:-136}"  # Default to 136 columns
LINES="${4:-41}"  # Default to 41 lines
FPS="${5:-30}"    # Default to 30 fps

# Calculate window dimensions based on font size (approx 7.5px×12.5px per char)
CHAR_WIDTH=7.5
CHAR_HEIGHT=12.5
W=$(echo "$COLS * $CHAR_WIDTH" | bc | cut -d. -f1)
H=$(echo "$LINES * $CHAR_HEIGHT" | bc | cut -d. -f1)

SCRIPT_PATH="$(realpath ./run.sh)"
LAUNCH_SCRIPT="./_launch.sh"  # Renamed to _launch.sh

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

# Write the command to a temporary script
echo "$COMMAND" > "$TMPDIR/command.sh"
chmod +x "$TMPDIR/command.sh"

env -i \
  HOME="$FAKE_HOME" \
  PATH="$PATH" \
  DISPLAY=:99 \
  XDG_RUNTIME_DIR="$RUNTIME_DIR" \
  XDG_CONFIG_HOME="$CONFIG_DIR" \
  XDG_DATA_HOME="$DATA_DIR" \
  W="$W" H="$H" OUT="$OUT" FPS="$FPS" \
  COLS="$COLS" LINES="$LINES" \
  SCRIPT_PATH="$TMPDIR/command.sh" \
  bash "$LAUNCH_SCRIPT"
