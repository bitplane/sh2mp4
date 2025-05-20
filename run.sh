#!/usr/bin/env bash
set -euo pipefail

# Script can receive command, output, cols, lines, fps as arguments
COMMAND="${1:-echo 'No command specified'}"
COLS="${COLS:-$(tput cols)}"
LINES="${LINES:-$(tput lines)}"

# Execute the command
eval "$COMMAND"
