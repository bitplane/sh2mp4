#!/usr/bin/env bash
set -euo pipefail

# Ensure UTF-8 locale is used for proper box-drawing and Unicode handling
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANGUAGE=en_US.UTF-8

# Sanity check: fail early if locale isn't available
locale -a | grep -qi 'en_US.utf8' || {
  echo "Missing locale: en_US.UTF-8. You may need: sudo locale-gen en_US.UTF-8"
  exit 1
}

# Required env
: "${DISPLAY:=:99}"
: "${W:?}"               # e.g. 1280
: "${H:?}"               # e.g. 720
: "${OUT:?}"             # e.g. output.mp4
: "${SCRIPT_PATH:?}"     # e.g. ./run.sh
: "${FPS:=30}"           # Default to 30 fps
: "${COLS:=136}"         # Default to 136 columns
: "${LINES:=41}"         # Default to 41 lines

# Start virtual X server
Xvfb "$DISPLAY" -screen 0 "${W}x${H}x24" +extension RANDR &
XVFB_PID=$!
sleep 1

# Start minimal window manager
DISPLAY=$DISPLAY openbox &
WM_PID=$!
sleep 1

# Move mouse cursor off-screen (if xdotool available)
if command -v xdotool >/dev/null 2>&1; then
  DISPLAY=$DISPLAY xdotool mousemove $W $H
fi

# Ensure we clean up even if things crash
cleanup() {
  echo "Cleaning up..."
  kill "$TERM_PID" "$WM_PID" "$XVFB_PID" 2>/dev/null || true
  wait "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Launch xterm with proper font, UTF-8, and box-drawing - no titlebar/decorations
DISPLAY=$DISPLAY xterm \
  -fa 'DejaVu Sans Mono' -fs 6 \
  -bg black -fg white \
  -geometry "${COLS}x${LINES}" \
  -T "no_title" \
  +sb \
  -e "$SCRIPT_PATH" &
TERM_PID=$!
sleep 1

# Resize to match actual pixel dimensions and remove window decorations
for i in {1..50}; do
  WID=$(DISPLAY=$DISPLAY xdotool search --onlyvisible --class xterm | head -n1 || true)
  if [ -n "$WID" ]; then
    # Set window size
    DISPLAY=$DISPLAY wmctrl -ir "$WID" -e 0,0,0,"$W","$H"
    # Remove window decorations (titlebar)
    DISPLAY=$DISPLAY xprop -id "$WID" -f _MOTIF_WM_HINTS 32c -set _MOTIF_WM_HINTS "0x2, 0x0, 0x0, 0x0, 0x0"
    break
  fi
  sleep 0.1
done

# Record the screen to output file
ffmpeg -y -f x11grab -framerate "$FPS" -video_size "${W}x${H}" -i "$DISPLAY" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$OUT"
