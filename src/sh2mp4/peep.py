"""
Live preview of X displays for debugging recordings
"""

import argparse
import asyncio
import sys

from . import __version__
from .xserver import list_running_xservers, get_newest_xserver, test_display_connection


async def list_displays() -> int:
    """List all available X displays"""
    servers = await list_running_xservers()

    if not servers:
        print("No running X servers found")
        return 1

    print("Running X servers:")
    print("Display  PID     Status")
    print("-------  ------  ------")

    for server in servers:
        pid_str = str(server.pid) if server.pid else "unknown"

        # Test if we can connect
        can_connect = await test_display_connection(server.display_name)
        status = "active" if can_connect else "inactive"

        print(f"{server.display_name:<7}  {pid_str:<6}  {status}")

    return 0


async def peep_display(display_name: str, interval: float = 0.1) -> int:
    """Monitor an X display and show live preview using chafa"""

    # Test connection first
    if not await test_display_connection(display_name):
        print(f"Cannot connect to display {display_name}")
        return 1

    print(f"Monitoring {display_name} (press Ctrl+C to stop)")

    try:
        while True:
            # Take screenshot
            screenshot_proc = await asyncio.create_subprocess_exec(
                "import",
                "-window",
                "root",
                "-display",
                display_name,
                "screenshot.png",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            await screenshot_proc.wait()

            if screenshot_proc.returncode == 0:
                # Display with chafa
                chafa_proc = await asyncio.create_subprocess_exec(
                    "chafa",
                    "--polite=on",
                    "-c",
                    "16",
                    "screenshot.png",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )

                stdout, _ = await chafa_proc.communicate()

                if chafa_proc.returncode == 0:
                    # Clear screen and show image
                    print("\033[2J\033[H", end="")  # Clear screen and move to top
                    print(stdout.decode(), end="")
                else:
                    print("Failed to display with chafa")
            else:
                print(f"Failed to capture screenshot from {display_name}")

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\nPeep stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for peep command"""
    parser = argparse.ArgumentParser(
        description="Live preview of X displays for debugging recordings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool shows a live preview of X displays for monitoring recordings.
Useful for debugging when recordings appear blank or for monitoring progress.

Requirements:
  - chafa (for terminal image display)
  - imagemagick (for screenshots)

Examples:
  peep                    # Monitor newest running X server
  peep --display :1       # Monitor specific display
  peep --list             # List all running X servers
  peep --interval 0.5     # Update every 500ms
""",
    )

    parser.add_argument("--display", help="Display to monitor (default: newest running X server)")
    parser.add_argument("--list", action="store_true", help="List all running X servers")
    parser.add_argument("--interval", type=float, default=0.1, help="Update interval in seconds (default: 0.1)")
    parser.add_argument("--version", action="version", version=f"sh2mp4-peep {__version__}")

    return parser


async def main_async(args) -> int:
    """Async main function"""
    if args.list:
        return await list_displays()

    # Determine which display to monitor
    if args.display:
        display_name = args.display
    else:
        # Find the newest running X server
        newest = await get_newest_xserver()
        if newest:
            display_name = newest.display_name
            print(f"Auto-detected newest X server: {display_name}")
        else:
            print("No running X servers found. Try --list to see available displays.")
            return 1

    return await peep_display(display_name, args.interval)


def main() -> int:
    """Main entry point for peep command"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
