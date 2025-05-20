#!/usr/bin/env bash
# Terminal themes for sh2mp4
# Define your preferred color schemes here

# Default theme (can be overridden with THEME env var)
THEME=${THEME:-sh2mp4}

# Available themes
case "$THEME" in
  tango)
    # Tango-based theme
    TERM_BG="#2e3436"
    TERM_FG="#d3d7cf"
    TERM_COLOR0="#2e3436"  # Black
    TERM_COLOR1="#cc0000"  # Red
    TERM_COLOR2="#4e9a06"  # Green
    TERM_COLOR3="#c4a000"  # Yellow
    TERM_COLOR4="#3465a4"  # Blue
    TERM_COLOR5="#75507b"  # Magenta
    TERM_COLOR6="#06989a"  # Cyan
    TERM_COLOR7="#d3d7cf"  # Light gray
    TERM_COLOR8="#555753"  # Dark gray
    TERM_COLOR9="#ef2929"  # Bright red
    TERM_COLOR10="#8ae234" # Bright green
    TERM_COLOR11="#fce94f" # Bright yellow
    TERM_COLOR12="#729fcf" # Bright blue
    TERM_COLOR13="#ad7fa8" # Bright magenta
    TERM_COLOR14="#34e2e2" # Bright cyan
    TERM_COLOR15="#eeeeec" # White
    ;;
    
  dark)
    # Dark theme with high contrast
    TERM_BG="#000000"
    TERM_FG="#ffffff"
    TERM_COLOR0="#000000"  # Black
    TERM_COLOR1="#cd0000"  # Red
    TERM_COLOR2="#00cd00"  # Green
    TERM_COLOR3="#cdcd00"  # Yellow
    TERM_COLOR4="#0000ee"  # Blue
    TERM_COLOR5="#cd00cd"  # Magenta
    TERM_COLOR6="#00cdcd"  # Cyan
    TERM_COLOR7="#e5e5e5"  # Light gray
    TERM_COLOR8="#7f7f7f"  # Dark gray
    TERM_COLOR9="#ff0000"  # Bright red
    TERM_COLOR10="#00ff00" # Bright green
    TERM_COLOR11="#ffff00" # Bright yellow
    TERM_COLOR12="#5c5cff" # Bright blue
    TERM_COLOR13="#ff00ff" # Bright magenta
    TERM_COLOR14="#00ffff" # Bright cyan
    TERM_COLOR15="#ffffff" # White
    ;;
    
  light)
    # Light theme
    TERM_BG="#ffffff"
    TERM_FG="#000000"
    TERM_COLOR0="#000000"  # Black
    TERM_COLOR1="#990000"  # Red
    TERM_COLOR2="#006600"  # Green
    TERM_COLOR3="#999900"  # Yellow
    TERM_COLOR4="#0000cc"  # Blue
    TERM_COLOR5="#990099"  # Magenta
    TERM_COLOR6="#009999"  # Cyan
    TERM_COLOR7="#cccccc"  # Light gray
    TERM_COLOR8="#666666"  # Dark gray
    TERM_COLOR9="#cc0000"  # Bright red
    TERM_COLOR10="#00aa00" # Bright green
    TERM_COLOR11="#cccc00" # Bright yellow
    TERM_COLOR12="#0000ff" # Bright blue
    TERM_COLOR13="#cc00cc" # Bright magenta
    TERM_COLOR14="#00cccc" # Bright cyan
    TERM_COLOR15="#ffffff" # White
    ;;
    
  solarized-dark)
    # Solarized Dark theme
    TERM_BG="#002b36"
    TERM_FG="#839496"
    TERM_COLOR0="#073642"  # Black
    TERM_COLOR1="#dc322f"  # Red
    TERM_COLOR2="#859900"  # Green
    TERM_COLOR3="#b58900"  # Yellow
    TERM_COLOR4="#268bd2"  # Blue
    TERM_COLOR5="#d33682"  # Magenta
    TERM_COLOR6="#2aa198"  # Cyan
    TERM_COLOR7="#eee8d5"  # Light gray
    TERM_COLOR8="#002b36"  # Dark gray
    TERM_COLOR9="#cb4b16"  # Bright red
    TERM_COLOR10="#586e75" # Bright green
    TERM_COLOR11="#657b83" # Bright yellow
    TERM_COLOR12="#839496" # Bright blue
    TERM_COLOR13="#6c71c4" # Bright magenta
    TERM_COLOR14="#93a1a1" # Bright cyan
    TERM_COLOR15="#fdf6e3" # White
    ;;
  *|sh2mp4)
    TERM_BG="#000000"
    TERM_FG="#ffffff"
    TERM_COLOR0="#2e3436"  # Black
    TERM_COLOR1="#cc0000"  # Red
    TERM_COLOR2="#4e9a06"  # Green
    TERM_COLOR3="#c4a000"  # Yellow
    TERM_COLOR4="#346da4"  # Blue
    TERM_COLOR5="#75507b"  # Magenta
    TERM_COLOR6="#06989a"  # Cyan
    TERM_COLOR7="#d3d7cf"  # Light gray
    TERM_COLOR8="#555753"  # Dark gray
    TERM_COLOR9="#ef2929"  # Bright red
    TERM_COLOR10="#8ae234" # Bright green
    TERM_COLOR11="#fce94f" # Bright yellow
    TERM_COLOR12="#729fcf" # Bright blue
    TERM_COLOR13="#ad7fa8" # Bright magenta
    TERM_COLOR14="#34e2e2" # Bright cyan
    TERM_COLOR15="#eeeeec" # White
    ;;
esac

# Export theme variables for use in xterm
export TERM_BG TERM_FG
export TERM_COLOR0 TERM_COLOR1 TERM_COLOR2 TERM_COLOR3 TERM_COLOR4 TERM_COLOR5 TERM_COLOR6 TERM_COLOR7
export TERM_COLOR8 TERM_COLOR9 TERM_COLOR10 TERM_COLOR11 TERM_COLOR12 TERM_COLOR13 TERM_COLOR14 TERM_COLOR15
