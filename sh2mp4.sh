#!/usr/bin/env bash
set -euxo pipefail  # Added -x for debugging

# Parse arguments
COMMAND="${1:-asciinema play /home/gaz/Videos/asciinema/faster.cast}"
OUT="${2:-output.mp4}"
COLS="${3:-$(tput cols)}"  # Use current terminal width if not specified
LINES="${4:-$(tput lines)}"  # Use current terminal height if not specified
FPS="${5:-30}"    # Default to 30 fps
FONT="${6:-DejaVu Sans Mono}"  # Default font
FONT_SIZE="${7:-12}"  # Default to 12pt font
THEME="${8:-sh2mp4}"  # Default to sh2mp4 theme

# Calculate character dimensions based on font size
# Based on measurements from measure_fonts.py for DejaVu Sans Mono
case "$FONT_SIZE" in
    4)  CHAR_WIDTH=3; CHAR_HEIGHT=7 ;;
    6)  CHAR_WIDTH=5; CHAR_HEIGHT=10 ;;
    8)  CHAR_WIDTH=6; CHAR_HEIGHT=13 ;;
    10) CHAR_WIDTH=8; CHAR_HEIGHT=17 ;;
    12) CHAR_WIDTH=10; CHAR_HEIGHT=19 ;;
    14) CHAR_WIDTH=11; CHAR_HEIGHT=23 ;;
    16) CHAR_WIDTH=13; CHAR_HEIGHT=26 ;;
    18) CHAR_WIDTH=14; CHAR_HEIGHT=29 ;;
    20) CHAR_WIDTH=16; CHAR_HEIGHT=32 ;;
    *) 
        echo "Warning: Unsupported font size $FONT_SIZE, using defaults for size 12"
        CHAR_WIDTH=10; CHAR_HEIGHT=19 ;;
esac
W=$(echo "$COLS * $CHAR_WIDTH" | bc | cut -d. -f1)
H=$(echo "$LINES * $CHAR_HEIGHT" | bc | cut -d. -f1)

# Ensure dimensions are even (required for h264 encoding)
W=$((W + (W % 2)))  # Add 1 if odd
H=$((H + (H % 2)))  # Add 1 if odd

# Print recording information
echo "Recording: $COMMAND"
echo "Output: $OUT (${W}x${H}, ${FPS}fps, font: $FONT ${FONT_SIZE}pt, theme: $THEME)"

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
  # Kill the stdin pipe process if it's running
  if [ -n "${PIPE_PID:-}" ]; then
    kill "$PIPE_PID" 2>/dev/null || true
  fi
  
  # Give Xvfb and other processes a gentle shutdown first
  pkill -TERM -f "Xvfb :99" 2>/dev/null || true
  sleep 0.5
  # Force kill anything still hanging around
  pkill -9 -f "Xvfb :99" 2>/dev/null || true
  
  # Clean up temporary files
  rm -rf "$TMPDIR"
}
trap cleanup EXIT INT TERM HUP

# Create a named pipe (FIFO) for stdin
FIFO="$TMPDIR/stdin.fifo"
mkfifo "$FIFO"
chmod 600 "$FIFO"

# Write the command to a temporary script that reads from the FIFO
cat > "$TMPDIR/command.sh" << EOF
#!/usr/bin/env bash
set -euxo pipefail  # Added -x for debugging

# Source the environment variables
source "$TMPDIR/env.sh"

# Execute the actual command, reading from the FIFO
$COMMAND < "$FIFO"

# Exit explicitly after command completes
exit 0
EOF
chmod +x "$TMPDIR/command.sh"

# Set up background process to pipe stdin to the FIFO with disabled buffering
stdbuf -i0 -o0 -e0 cat <&0 > "$FIFO" &
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
export THEME="$THEME"
EOF
chmod +x "$TMPDIR/env.sh"

# Starting recording process

env -i \
  HOME="$FAKE_HOME" \
  PATH="$PATH" \
  DISPLAY=:99 \
  XDG_RUNTIME_DIR="$RUNTIME_DIR" \
  XDG_CONFIG_HOME="$CONFIG_DIR" \
  XDG_DATA_HOME="$DATA_DIR" \
  W="$W" H="$H" OUT="$OUT" FPS="$FPS" \
  COLS="$COLS" LINES="$LINES" FONT="$FONT" FONT_SIZE="$FONT_SIZE" THEME="$THEME" \
  SCRIPT_PATH="$TMPDIR/command.sh" \
  bash "$LAUNCH_SCRIPT"
