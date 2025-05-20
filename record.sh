#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
COMMAND="${1:-asciinema play /home/gaz/Videos/asciinema/faster.cast}"
OUT="${2:-output.mp4}"
COLS="${3:-136}"  # Default to 136 columns
LINES="${4:-41}"  # Default to 41 lines
FPS="${5:-30}"    # Default to 30 fps
FONT="${6:-DejaVu Sans Mono}"  # Default font

# Calculate window dimensions based on font size (font size 6)
# From measurement: width=5px, height=10px
CHAR_WIDTH=5
CHAR_HEIGHT=10
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
cat > "$TMPDIR/command.sh" << EOF
#!/usr/bin/env bash
set -euo pipefail

# Source the environment variables
source "$TMPDIR/env.sh"

# Execute the actual command
$COMMAND
EOF
chmod +x "$TMPDIR/command.sh"

# Create environment file to pass variables to command script
cat > "$TMPDIR/env.sh" << EOF
export COLS="$COLS"
export LINES="$LINES"
export FPS="$FPS"
export FONT="$FONT"
export W="$W"
export H="$H"
export OUT="$OUT"
EOF
chmod +x "$TMPDIR/env.sh"

env -i \
  HOME="$FAKE_HOME" \
  PATH="$PATH" \
  DISPLAY=:99 \
  XDG_RUNTIME_DIR="$RUNTIME_DIR" \
  XDG_CONFIG_HOME="$CONFIG_DIR" \
  XDG_DATA_HOME="$DATA_DIR" \
  W="$W" H="$H" OUT="$OUT" FPS="$FPS" \
  COLS="$COLS" LINES="$LINES" FONT="$FONT" \
  SCRIPT_PATH="$TMPDIR/command.sh" \
  bash "$LAUNCH_SCRIPT"
