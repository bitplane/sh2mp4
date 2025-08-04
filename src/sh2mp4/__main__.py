"""
Main entry point for sh2mp4
"""

import asyncio
import sys
from pathlib import Path

from .display import DisplayManager
from .terminal import TerminalManager
from .recorder import Recorder
from .themes import get_theme
from .fonts import calculate_window_dimensions
from .check_deps import main as check_dependencies
from .measure_fonts import main as measure_fonts
from .args import parse_and_validate_args


async def record_command(args) -> int:
    """Main recording function"""

    # Args are now ready to use - no additional processing needed
    if args.cast_file:
        print(f"Cast file dimensions: {args.cols}x{args.lines} characters (optimized)")

    # Calculate window dimensions
    width, height = calculate_window_dimensions(args.cols, args.lines, args.font, args.font_size)

    print(f"Recording: {args.command}")

    # Show speed info if using high-speed conversion
    speed_info = ""
    if args.recording_fps != args.fps:
        speed_multiplier = args.recording_fps // args.fps
        speed_info = f", recording at {speed_multiplier}x speed ({args.recording_fps}fps)"

    print(
        f"Output: {args.output} ({width}x{height}, {args.fps}fps{speed_info}, "
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
            recorder = Recorder(
                display.display_name,
                width,
                height,
                args.fps,
                Path(args.output),
                watch=args.watch,
                recording_fps=args.recording_fps,
                debug=getattr(args, "debug", False),
            )

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


def main() -> int:
    """Main entry point"""
    args = parse_and_validate_args()

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

    # Check dependencies before recording (silently)
    from .check_deps import check_runtime_dependencies

    missing = check_runtime_dependencies(cast_file_mode=bool(args.cast_file))
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
