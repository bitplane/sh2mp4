#!/bin/bash
set -euo pipefail

# Test script to record a command and extract a middle frame
# Usage: ./tests/test-single-frame.sh "command to test"

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"command to test\""
    echo "Example: $0 \"ls -la\""
    exit 1
fi

COMMAND="$1"
OUTPUT_VIDEO="test-frame.mp4"
OUTPUT_FRAME="test-frame.png"

echo "Testing command: $COMMAND"

# Clean up any existing files
rm -f "$OUTPUT_VIDEO" "$OUTPUT_FRAME"

# Source venv and record with sleeps
echo "Recording..."
source .venv/bin/activate
sh2mp4 "sleep 3; $COMMAND; sleep 3" "$OUTPUT_VIDEO"

# Get video duration and calculate middle frame
echo "Extracting middle frame..."
DURATION=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_VIDEO")
MIDDLE_TIME=$(echo "$DURATION / 2" | bc -l)

# Extract middle frame
ffmpeg -v quiet -i "$OUTPUT_VIDEO" -ss "$MIDDLE_TIME" -vframes 1 -y "$OUTPUT_FRAME"

echo "Done! Video: $OUTPUT_VIDEO, Frame: $OUTPUT_FRAME"
echo "View the frame with: xdg-open $OUTPUT_FRAME"