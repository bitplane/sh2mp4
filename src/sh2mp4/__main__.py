"""
Main entry point for sh2mp4
"""

import asyncio
import sys
import signal
from pathlib import Path

from .display import DisplayManager
from .terminal import TerminalManager
from .recorder import Recorder
from .themes import get_theme
from .fonts import calculate_window_dimensions
from .check_deps import main as check_dependencies, check_runtime_dependencies
from .measure_fonts import main as measure_fonts
from .args import parse_and_validate_args


async def record_command(args) -> int:
    """Main recording function"""

    # Args are now ready to use - no additional processing needed
    if args.cast_file:
        print(f"Cast file dimensions: {args.cols}x{args.lines} characters (optimized)")

    # Calculate window dimensions
    try:
        async with DisplayManager() as measurement_display:
            await measurement_display._start_xvfb(640, 480)
            width, height = calculate_window_dimensions(
                args.cols, args.lines, args.font, args.font_size, measurement_display.display_name
            )
    except Exception as e:
        print(f"Error measuring font: {e}", file=sys.stderr)
        return 1

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

            terminal = TerminalManager(
                display.display_name, theme, args.font, args.font_size, args.cols, args.lines, width, height
            )
            async with terminal:
                await terminal.start(args.command, cast_mode=bool(args.cast_file))
                recorder = Recorder(
                    display.display_name,
                    width,
                    height,
                    args.fps,
                    Path(args.output),
                    watch=args.watch,
                    recording_fps=args.recording_fps,
                    debug=args.debug,
                )
                async with recorder:
                    await recorder.start()
                    print("Recording started...")

                    # Signal that recorder is ready so command can proceed
                    recorder.begin_content()
                    terminal.signal_recorder_ready()
                    print("Recording... (waiting for command to complete)")

                    # Wait for command to complete
                    command_task = asyncio.create_task(terminal.wait_for_completion())
                    encoder_task = asyncio.create_task(recorder.wait_for_failure())
                    try:
                        done, _ = await asyncio.wait([command_task, encoder_task], return_when=asyncio.FIRST_COMPLETED)
                        if encoder_task in done:
                            await encoder_task
                        exit_code = await command_task
                        recorder.end_content(terminal.playback_timing() if args.cast_file and exit_code == 0 else None)
                        await asyncio.sleep(0.5 * args.fps / args.recording_fps)
                    finally:
                        for task in (command_task, encoder_task):
                            task.cancel()
                        await asyncio.gather(command_task, encoder_task, return_exceptions=True)

                    print("Command completed, stopping recording...")

                    # Stop recording
                    encoder_status = await recorder.stop()
                    if encoder_status != 0:
                        raise RuntimeError(recorder.error_message(f"FFmpeg failed (status {encoder_status})"))

                    await recorder.encode()
                    print(f"Recording complete: {args.output}")
                    return exit_code

    except KeyboardInterrupt:
        print("Recording interrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def run_recording(args):
    """Route termination signals through the same cleanup as cancellation."""
    loop = asyncio.get_running_loop()
    task = asyncio.current_task()
    received = None

    def cancel(signum):
        nonlocal received
        if received is None:
            received = signum
            task.cancel()

    for signum in (signal.SIGTERM, signal.SIGHUP):
        loop.add_signal_handler(signum, cancel, signum)
    try:
        return await record_command(args)
    except asyncio.CancelledError:
        if received is not None:
            return 128 + received
        raise
    finally:
        for signum in (signal.SIGTERM, signal.SIGHUP):
            loop.remove_signal_handler(signum)


def main() -> int:
    """Main entry point"""
    args = parse_and_validate_args()

    # Handle utility modes
    if args.check_deps:
        return check_dependencies()

    # Check dependencies before recording (silently)
    missing = check_runtime_dependencies(cast_file_mode=bool(args.cast_file))
    if missing:
        print(f"Error: Missing required dependencies: {', '.join(missing)}", file=sys.stderr)
        print("Run 'sh2mp4 --check-deps' for detailed information", file=sys.stderr)
        return 1

    if args.measure_fonts:
        return measure_fonts([])

    # Run the async recording function
    try:
        return asyncio.run(run_recording(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
