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

# Load theme settings
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "${SCRIPT_DIR}/themes.sh"

# Required env - no defaults for critical dimensions
: "${DISPLAY:=:99}"
: "${W:?}"               # e.g. 1280
: "${H:?}"               # e.g. 720
: "${OUT:?}"             # e.g. output.mp4
: "${SCRIPT_PATH:?}"     # e.g. ./run.sh
: "${FPS:?}"             # No default, must be passed from caller
: "${COLS:?}"            # No default, must be passed from caller
: "${LINES:?}"           # No default, must be passed from caller
: "${FONT:?}"            # No default, must be passed from caller

# Start virtual X server
Xvfb "$DISPLAY" -screen 0 "${W}x${H}x24" +extension RANDR &
XVFB_PID=$!
sleep 1

# Start minimal window manager with no decorations configuration
mkdir -p "$HOME/.config/openbox"
cat > "$HOME/.config/openbox/rc.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <applications>
    <application class="*">
      <decor>no</decor>
      <maximized>yes</maximized>
    </application>
  </applications>
</openbox_config>
EOF

DISPLAY=$DISPLAY openbox --config-file "$HOME/.config/openbox/rc.xml" &
WM_PID=$!
sleep 1

# Hide the mouse cursor
# Method 1: Try using unclutter if available
if command -v unclutter >/dev/null 2>&1; then
  echo "Using unclutter to hide cursor"
  DISPLAY=$DISPLAY unclutter -idle 0 -root &
  UNCLUTTER_PID=$!
# Method 2: Move cursor far off-screen as fallback
elif command -v xdotool >/dev/null 2>&1; then
  echo "Moving cursor off-screen"
  # Move to far bottom right corner
  DISPLAY=$DISPLAY xdotool mousemove 9999 9999
fi

# Ensure we clean up even if things crash
cleanup() {
  echo "Cleaning up..."
  # Kill unclutter if it was started
  if [ -n "${UNCLUTTER_PID:-}" ]; then
    kill "$UNCLUTTER_PID" 2>/dev/null || true
  fi
  kill "$TERM_PID" "$WM_PID" "$XVFB_PID" 2>/dev/null || true
  wait "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM HUP

# Launch xterm with proper font, UTF-8, and box-drawing - no titlebar/decorations
DISPLAY=$DISPLAY xterm \
  -fa "$FONT" -fs "$FONT_SIZE" \
  -bg "${TERM_BG}" -fg "${TERM_FG}" \
  -xrm "XTerm*color0: ${TERM_COLOR0}" \
  -xrm "XTerm*color1: ${TERM_COLOR1}" \
  -xrm "XTerm*color2: ${TERM_COLOR2}" \
  -xrm "XTerm*color3: ${TERM_COLOR3}" \
  -xrm "XTerm*color4: ${TERM_COLOR4}" \
  -xrm "XTerm*color5: ${TERM_COLOR5}" \
  -xrm "XTerm*color6: ${TERM_COLOR6}" \
  -xrm "XTerm*color7: ${TERM_COLOR7}" \
  -xrm "XTerm*color8: ${TERM_COLOR8}" \
  -xrm "XTerm*color9: ${TERM_COLOR9}" \
  -xrm "XTerm*color10: ${TERM_COLOR10}" \
  -xrm "XTerm*color11: ${TERM_COLOR11}" \
  -xrm "XTerm*color12: ${TERM_COLOR12}" \
  -xrm "XTerm*color13: ${TERM_COLOR13}" \
  -xrm "XTerm*color14: ${TERM_COLOR14}" \
  -xrm "XTerm*color15: ${TERM_COLOR15}" \
  -geometry "${COLS}x${LINES}" \
  -T "no_title" \
  +sb \
  -b 0 \
  -bd "${TERM_BG}" \
  -bw 0 \
  +maximized \
  -e "$SCRIPT_PATH" &
TERM_PID=$!
sleep 1

# Resize to match actual pixel dimensions and remove window decorations
for i in {1..50}; do
  WID=$(DISPLAY=$DISPLAY xdotool search --onlyvisible --class xterm | head -n1 || true)
  if [ -n "$WID" ]; then
    echo "Found xterm window ID: $WID"
    
    # Set window size and position (0,0 coordinates, width x height)
    DISPLAY=$DISPLAY wmctrl -ir "$WID" -e 0,0,0,"$W","$H"
    
    # Apply both decoration removal methods
    
    # Method 1: MOTIF hints
    DISPLAY=$DISPLAY xprop -id "$WID" -f _MOTIF_WM_HINTS 32c -set _MOTIF_WM_HINTS "0x2, 0x0, 0x0, 0x0, 0x0"
    
    # Method 2: Openbox undecorated property
    DISPLAY=$DISPLAY wmctrl -i -r "$WID" -b add,undecorated
    
    # Also make it full screen for good measure
    DISPLAY=$DISPLAY wmctrl -i -r "$WID" -b add,fullscreen
    
    echo "Window configured and decorations removed."
    break
  fi
  sleep 0.1
done

# Record the screen to output file
ffmpeg -y -f x11grab -framerate "$FPS" -video_size "${W}x${H}" -i "$DISPLAY" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "$OUT"
