"""
Font measurement utility for sh2mp4
"""

import argparse
import asyncio
import sys

from . import __version__
from .fonts import measure_all_fonts, measure_font
from .display import DisplayManager


def main(argv=None) -> int:
    """Main entry point for measure-fonts command"""
    parser = argparse.ArgumentParser(
        description="Measure character dimensions of monospace fonts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This utility measures the pixel dimensions of monospace fonts at various sizes.
Useful for determining optimal font/size combinations for video recording.

Examples:
  measure-fonts                           # Measure all common fonts
  measure-fonts --font "Ubuntu Mono"     # Measure specific font
  measure-fonts --size 14                # Measure specific size only
""",
    )

    parser.add_argument("--font", help="Measure specific font only")
    parser.add_argument("--size", type=int, help="Measure specific size only")
    parser.add_argument("--version", action="version", version=f"sh2mp4-measure-fonts {__version__}")

    args = parser.parse_args(argv)

    async def measure():
        async with DisplayManager() as display:
            await display._start_xvfb(640, 480)
            if args.font:
                sizes = [args.size] if args.size else [4, 6, 8, 10, 12, 14, 16, 18, 20]
                results = {args.font: {size: measure_font(args.font, size, display.display_name) for size in sizes}}
            else:
                results = measure_all_fonts(display.display_name)
            for name, sizes in results.items():
                for size, metrics in sizes.items():
                    if args.size is None or size == args.size:
                        print(f"{name} {size} {metrics.width}x{metrics.height}")
        return 0

    try:
        return asyncio.run(measure())
    except Exception as e:
        print(f"Error measuring fonts: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
