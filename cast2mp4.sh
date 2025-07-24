#!/usr/bin/env bash
set -euo pipefail

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <cast_file> [output.mp4] [fps] [font] [font_size] [theme]"
    echo "Converts an asciinema .cast file to mp4"
    exit 1
fi

CAST_FILE="$1"
OUTPUT="${2:-output.mp4}"
FPS="${3:-30}"
FONT="${4:-DejaVu Sans Mono}"
FONT_SIZE="${5:-12}"
THEME="${6:-sh2mp4}"

# Check if cast file exists
if [ ! -f "$CAST_FILE" ]; then
    echo "Error: Cast file '$CAST_FILE' not found"
    exit 1
fi

# Get absolute path of cast file
CAST_FILE="$(realpath "$CAST_FILE")"

# Extract width and height from first line of cast file using jq
if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required. Please install it or run ./configure"
    exit 1
fi

HEADER=$(head -n1 "$CAST_FILE")
WIDTH=$(echo "$HEADER" | jq -r '.width // empty')
HEIGHT=$(echo "$HEADER" | jq -r '.height // empty')

if [ -z "$WIDTH" ] || [ -z "$HEIGHT" ]; then
    echo "Error: Could not extract width/height from cast file"
    echo "Header: $HEADER"
    exit 1
fi

echo "Cast file dimensions: ${WIDTH}x${HEIGHT} characters"

# Convert to mp4 using sh2mp4.sh
# Using bash -c to ensure proper shell environment and -i 1 for max idle time
./sh2mp4.sh "bash -c 'asciinema play -i 1 \"$CAST_FILE\"'" "$OUTPUT" "$WIDTH" "$HEIGHT" "$FPS" "$FONT" "$FONT_SIZE" "$THEME"