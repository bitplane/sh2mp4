"""
Main entry point for sh2mp4
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import __version__
from .display import DisplayManager
from .terminal import TerminalManager
from .recorder import Recorder
from .themes import get_theme, list_themes
from .fonts import calculate_window_dimensions
from .check_deps import main as check_dependencies
from .measure_fonts import main as measure_fonts


async def record_command(args) -> int:
    """Main recording function"""
    # Calculate window dimensions
    width, height = calculate_window_dimensions(args.cols, args.lines, args.font, args.font_size)

    print(f"Recording: {args.command}")
    print(
        f"Output: {args.output} ({width}x{height}, {args.fps}fps, "
        f"font: {args.font} {args.font_size}pt, theme: {args.theme})"
    )

    # Get theme
    theme = get_theme(args.theme)

    try:
        # Start display manager
        async with DisplayManager(args.display) as display:
            await display.start(width, height)

            # Wait a moment for display to be ready
            await asyncio.sleep(1)

            # Start recording first (before command execution begins)
            recorder = Recorder(display.display_name, width, height, args.fps, Path(args.output), watch=args.watch)

            async with recorder:
                await recorder.start()
                print("Recording started...")

                # Now start terminal and command
                terminal = TerminalManager(
                    display.display_name, theme, args.font, args.font_size, args.cols, args.lines, width, height
                )

                async with terminal:
                    await terminal.start(args.command)

                    # Signal that recorder is ready so command can proceed
                    terminal.signal_recorder_ready()
                    print("Recording... (waiting for command to complete)")

                    # Wait for command to complete
                    exit_code = await terminal.wait_for_completion()

                    print("Command completed, stopping recording...")

                    # Stop recording
                    await recorder.stop()

                    print(f"Recording complete: {args.output}")
                    return exit_code

    except KeyboardInterrupt:
        print("Recording interrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        description="Record shell commands to MP4 videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available themes: {', '.join(list_themes())}

Examples:
  sh2mp4 "ls -la" demo.mp4
  sh2mp4 "htop" htop.mp4 --cols 120 --lines 40 --theme dark
  sh2mp4 "timeout 10 cmatrix" matrix.mp4 --font-size 14
  sh2mp4 --check-deps  # Check if all dependencies are installed
  sh2mp4 --measure-fonts  # Measure available fonts
""",
    )

    parser.add_argument("command", nargs="?", help="Command to record")
    parser.add_argument("output", nargs="?", default="output.mp4", help="Output MP4 file (default: output.mp4)")

    # Terminal dimensions
    parser.add_argument(
        "--cols",
        type=int,
        default=int(os.popen("tput cols 2>/dev/null || echo 80").read().strip()),
        help="Terminal width in characters (default: current terminal width)",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=int(os.popen("tput lines 2>/dev/null || echo 24").read().strip()),
        help="Terminal height in characters (default: current terminal height)",
    )

    # Video settings
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")

    # Font settings
    parser.add_argument("--font", default="DejaVu Sans Mono", help="Font family (default: DejaVu Sans Mono)")
    parser.add_argument("--font-size", type=int, default=12, help="Font size in points (default: 12)")

    # Theme
    parser.add_argument("--theme", default="sh2mp4", choices=list_themes(), help="Color theme (default: sh2mp4)")

    # Display
    parser.add_argument("--display", type=int, help="X display number to use (default: auto-allocate)")

    # Watch mode
    parser.add_argument("--watch", action="store_true", help="Show live preview during recording")

    # Utility modes
    parser.add_argument("--check-deps", action="store_true", help="Check if all dependencies are installed")
    parser.add_argument("--measure-fonts", action="store_true", help="Measure available monospace fonts")

    # Version
    parser.add_argument("--version", action="version", version=f"sh2mp4 {__version__}")

    return parser


def main() -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Handle utility modes
    if args.check_deps:
        return check_dependencies()

    if args.measure_fonts:
        # Run measure fonts with no arguments (measures all fonts)
        import sys

        original_argv = sys.argv
        sys.argv = [sys.argv[0]]  # Remove all arguments
        result = measure_fonts()
        sys.argv = original_argv
        return result

    # Validate that we have a command for recording mode
    if not args.command:
        parser.error("command is required when not using --check-deps or --measure-fonts")

    # Check dependencies before recording (silently)
    from .check_deps import check_command

    required_commands = ["xdotool", "wmctrl", "ffmpeg", "Xvfb", "openbox", "xterm", "unclutter"]
    missing = [cmd for cmd in required_commands if not check_command(cmd)]
    if missing:
        print(f"Error: Missing required dependencies: {', '.join(missing)}", file=sys.stderr)
        print("Run 'sh2mp4 --check-deps' for detailed information", file=sys.stderr)
        return 1

    # Run the async recording function
    try:
        return asyncio.run(record_command(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
