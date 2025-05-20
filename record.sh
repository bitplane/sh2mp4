#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
COMMAND="${1:-asciinema play /home/gaz/Videos/asciinema/faster.cast}"
OUT="${2:-output.mp4}"
COLS="${3:-$(tput cols)}"  # Use current terminal width if not specified
LINES="${4:-$(tput lines)}"  # Use current terminal height if not specified
FPS="${5:-30}"    # Default to 30 fps
FONT="${6:-DejaVu Sans Mono}"  # Default font

# Print terminal dimensions for debugging
echo "Terminal dimensions: $COLS columns x $LINES lines"

# Calculate window dimensions based on font size (font size 6)
# From measurement: width=5px, height=10px
CHAR_WIDTH=5
CHAR_HEIGHT=10
W=$(echo "$COLS * $CHAR_WIDTH" | bc | cut -d. -f1)
H=$(echo "$LINES * $CHAR_HEIGHT" | bc | cut -d. -f1)

# Ensure dimensions are even (required for h264 encoding)
W=$((W + (W % 2)))  # Add 1 if odd
H=$((H + (H % 2)))  # Add 1 if odd

# Print calculated dimensions
echo "Calculated window size: ${W}x${H} pixels (adjusted to be even)"

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
  # Kill the stdin pipe process if it's running
  if [ -n "${PIPE_PID:-}" ]; then
    kill "$PIPE_PID" 2>/dev/null || true
  fi
  pkill -f "Xvfb :99" 2>/dev/null || true
  rm -rf "$TMPDIR"
}
trap cleanup EXIT INT TERM

# Create a named pipe (FIFO) for stdin
FIFO="$TMPDIR/stdin.fifo"
mkfifo "$FIFO"
chmod 600 "$FIFO"

# Write the command to a temporary script that reads from the FIFO
cat > "$TMPDIR/command.sh" << EOF
#!/usr/bin/env bash
set -euo pipefail

# Source the environment variables
source "$TMPDIR/env.sh"

# Execute the actual command, reading from the FIFO
$COMMAND < "$FIFO"
EOF
chmod +x "$TMPDIR/command.sh"

# Set up background process to pipe stdin to the FIFO
# Use stdbuf to disable buffering if available
if command -v stdbuf >/dev/null 2>&1; then
  echo "Using stdbuf for unbuffered pipe"
  stdbuf -i0 -o0 -e0 cat <&0 > "$FIFO" &
else
  echo "stdbuf not available, using regular cat"
  cat <&0 > "$FIFO" &
fi
PIPE_PID=$!

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

# Print actual values being passed to _launch.sh
echo "Passing to _launch.sh: W=$W, H=$H, COLS=$COLS, LINES=$LINES, FPS=$FPS, FONT=$FONT"

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
