#!/usr/bin/env bash
set -euo pipefail

# Script can receive command, output, cols, lines, fps as arguments
COMMAND="${1:-echo 'No command specified'}"
COLS="${COLS:-$(tput cols)}"
LINES="${LINES:-$(tput lines)}"
FPS="${FPS:-30}"
FONT="${FONT:-DejaVu Sans Mono}"
W="${W:-$(echo "$COLS * 5" | bc | cut -d. -f1)}"
H="${H:-$(echo "$LINES * 10" | bc | cut -d. -f1)}"
OUT="${OUT:-output.mp4}"

# Print environment variables for debugging
echo "Environment variables:"
echo "COLS=$COLS, LINES=$LINES, FPS=$FPS"
echo "FONT=$FONT, W=$W, H=$H, OUT=$OUT"

# Execute the command
eval "$COMMAND"
