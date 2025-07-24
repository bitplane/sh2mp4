"""
Convert asciinema cast files to MP4 videos
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from . import __version__
from .__main__ import record_command
from .themes import list_themes


def parse_cast_header(cast_file: Path) -> tuple[int, int]:
    """Parse the asciinema cast file header to get dimensions"""
    try:
        with cast_file.open() as f:
            header_line = f.readline().strip()
            header = json.loads(header_line)

            width = header.get("width")
            height = header.get("height")

            if width is None or height is None:
                raise ValueError("Cast file missing width/height")

            return width, height

    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        raise ValueError(f"Failed to parse cast file: {e}")


async def convert_cast_to_mp4(args) -> int:
    """Convert asciinema cast file to MP4"""
    cast_file = Path(args.cast_file)

    if not cast_file.exists():
        print(f"Error: Cast file '{cast_file}' not found", file=sys.stderr)
        return 1

    # Extract dimensions from cast file
    try:
        width, height = parse_cast_header(cast_file)
        print(f"Cast file dimensions: {width}x{height} characters")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Create a modified args object for the main recorder
    class RecordArgs:
        def __init__(self):
            self.command = f'bash -c "asciinema play -i 1 \\"{cast_file.absolute()}\\""'
            self.output = args.output
            self.cols = width
            self.lines = height
            self.fps = args.fps
            self.font = args.font
            self.font_size = args.font_size
            self.theme = args.theme

    record_args = RecordArgs()
    return await record_command(record_args)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for cast2mp4"""
    parser = argparse.ArgumentParser(
        description="Convert asciinema cast files to MP4 videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available themes: {', '.join(list_themes())}

Examples:
  cast2mp4 recording.cast output.mp4
  cast2mp4 demo.cast demo.mp4 --theme dark --font-size 14
""",
    )

    parser.add_argument("cast_file", help="Asciinema cast file to convert")
    parser.add_argument("output", nargs="?", default="output.mp4", help="Output MP4 file (default: output.mp4)")

    # Video settings
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")

    # Font settings
    parser.add_argument("--font", default="DejaVu Sans Mono", help="Font family (default: DejaVu Sans Mono)")
    parser.add_argument("--font-size", type=int, default=12, help="Font size in points (default: 12)")

    # Theme
    parser.add_argument("--theme", default="sh2mp4", choices=list_themes(), help="Color theme (default: sh2mp4)")

    # Version
    parser.add_argument("--version", action="version", version=f"cast2mp4 {__version__}")

    return parser


def main() -> int:
    """Main entry point for cast2mp4"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        return asyncio.run(convert_cast_to_mp4(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
