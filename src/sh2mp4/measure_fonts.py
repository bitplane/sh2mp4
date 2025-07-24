"""
Font measurement utility for sh2mp4
"""

import argparse
import sys

from . import __version__
from .fonts import measure_all_fonts, measure_font


def main() -> int:
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

    args = parser.parse_args()

    try:
        if args.font and args.size:
            # Measure specific font and size
            metrics = measure_font(args.font, args.size)
            print(f"{args.font} {args.size} {metrics.width}x{metrics.height}")

        elif args.font:
            # Measure specific font at all sizes
            sizes = [4, 6, 8, 10, 12, 14, 16, 18, 20]
            for size in sizes:
                try:
                    metrics = measure_font(args.font, size)
                    print(f"{args.font} {size} {metrics.width}x{metrics.height}")
                except Exception:
                    continue

        else:
            # Measure all fonts
            results = measure_all_fonts()

            for font_name, sizes in results.items():
                for size, metrics in sizes.items():
                    print(f"{font_name} {size} {metrics.width}x{metrics.height}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
