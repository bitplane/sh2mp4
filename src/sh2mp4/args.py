"""
Argument parsing for sh2mp4
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .themes import list_themes


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments - simple and straightforward"""
    parser = argparse.ArgumentParser(
        description="Record shell commands to MP4 videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available themes: {', '.join(list_themes())}

Examples:
  sh2mp4 "ls -la" demo.mp4
  sh2mp4 "htop" htop.mp4 --cols 120 --lines 40 --theme dark
  sh2mp4 "timeout 10 cmatrix" matrix.mp4 --font-size 14
  sh2mp4 --cast-file recording.cast output.mp4
  sh2mp4 --cast-file demo.cast --speed 8x output.mp4
  sh2mp4 --check-deps
  sh2mp4 --measure-fonts
""",
    )

    # Positional arguments
    parser.add_argument("command", nargs="?", help="Command to record")
    parser.add_argument("output", nargs="?", default="output.mp4", help="Output MP4 file (default: output.mp4)")

    # Cast file mode
    parser.add_argument("--cast-file", help="Convert asciinema cast file to MP4")

    # Terminal dimensions
    parser.add_argument(
        "--cols",
        type=int,
        default=int(os.popen("tput cols 2>/dev/null || echo 80").read().strip()),
        help="Terminal width in characters",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=int(os.popen("tput lines 2>/dev/null || echo 24").read().strip()),
        help="Terminal height in characters",
    )

    # Video settings
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")

    # Font settings
    parser.add_argument("--font", default="DejaVu Sans Mono", help="Font family")
    parser.add_argument("--font-size", type=int, default=12, help="Font size in points")

    # Theme
    parser.add_argument("--theme", default="sh2mp4", choices=list_themes(), help="Color theme")

    # Display
    parser.add_argument("--display", type=int, help="X display number (auto-allocate if not specified)")

    # Options
    parser.add_argument("--watch", action="store_true", help="Show live preview during recording")
    parser.add_argument("--speed", choices=["2x", "4x", "8x"], help="Playback speed for cast files")
    parser.add_argument("--debug", action="store_true", help="Enable debug output from ffmpeg")

    # Utility modes
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--measure-fonts", action="store_true", help="Measure available fonts")

    # Version removed - use 'pip show sh2mp4' to get version info

    args = parser.parse_args(argv)

    # Check if cols/lines were explicitly provided by user
    user_provided_cols = "--cols" in (argv or sys.argv)
    user_provided_lines = "--lines" in (argv or sys.argv)

    # Process arguments to get them into "ready to execute" state
    if args.cast_file:
        # Cast file mode - process the cast file and modify args
        if not Path(args.cast_file).exists():
            parser.error(f"Cast file '{args.cast_file}' not found")

        # In cast file mode, if command is provided, treat it as output filename
        if args.command:
            args.output = args.command

        from .asciicast import get_cast_config

        # Parse speed multiplier
        speed_multiplier = 1.0
        if args.speed:
            speed_multiplier = float(args.speed.rstrip("x"))

        try:
            cast_config = get_cast_config(Path(args.cast_file), playback_speed=speed_multiplier, base_fps=args.fps)

            # Override args with cast file settings
            args.command = cast_config.command
            # Only override dimensions if user didn't explicitly specify them
            if not user_provided_cols:
                args.cols = cast_config.cols
            if not user_provided_lines:
                args.lines = cast_config.lines
            args.recording_fps = cast_config.recording_fps

        except ValueError as e:
            parser.error(str(e))

    elif not (args.check_deps or args.measure_fonts):
        # Normal recording mode
        if not args.command:
            parser.error("command is required")
        args.recording_fps = args.fps

        # Warn about speed without cast file
        if args.speed:
            print("Warning: --speed only applies to --cast-file mode, ignoring", file=sys.stderr)
            args.speed = None
    else:
        # Utility modes
        args.recording_fps = args.fps

    return args


# Keep the old function name for compatibility
def parse_and_validate_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Legacy wrapper - just parse args normally"""
    return parse_args(argv)
