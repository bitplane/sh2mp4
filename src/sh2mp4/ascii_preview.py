"""
Simple ASCII art preview for terminal display
"""

from pathlib import Path
from typing import Optional


def image_to_ascii(image_path: Path, width: int = 80, height: int = 24) -> Optional[str]:
    """Convert an image to ASCII art for terminal display"""
    try:
        from PIL import Image
    except ImportError:
        return None

    # ASCII characters from darkest to lightest
    ascii_chars = " .:-=+*#%@"

    try:
        # Open and resize image
        img = Image.open(image_path)

        # Calculate aspect ratio to maintain proportions
        # Terminal characters are typically 2x tall as they are wide
        term_aspect = height / width * 2
        img_aspect = img.height / img.width

        if img_aspect > term_aspect:
            # Image is taller, fit to height
            new_height = height
            new_width = int(height / img_aspect * 2)
        else:
            # Image is wider, fit to width
            new_width = width
            new_height = int(width * img_aspect / 2)

        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to grayscale
        img = img.convert("L")

        # Convert pixels to ASCII
        ascii_str = ""
        pixels = img.getdata()

        for i in range(0, len(pixels), new_width):
            row = pixels[i : i + new_width]
            ascii_row = ""
            for pixel in row:
                # Map pixel value (0-255) to ASCII character
                char_index = int(pixel / 256 * len(ascii_chars))
                if char_index >= len(ascii_chars):
                    char_index = len(ascii_chars) - 1
                ascii_row += ascii_chars[char_index]
            ascii_str += ascii_row + "\n"

        return ascii_str.rstrip()

    except Exception:
        return None


def colored_blocks_preview(image_path: Path, width: int = 80, height: int = 24) -> Optional[str]:
    """Convert image to colored Unicode block characters"""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        # Open and resize image
        img = Image.open(image_path)

        # Calculate dimensions (each block represents 2 vertical pixels)
        new_width = width
        new_height = height * 2

        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to RGB
        img = img.convert("RGB")

        output = []
        pixels = list(img.getdata())

        # Process pairs of rows
        for y in range(0, new_height, 2):
            row = []
            for x in range(new_width):
                # Get top and bottom pixels
                top_idx = y * new_width + x
                bottom_idx = (y + 1) * new_width + x if y + 1 < new_height else top_idx

                if top_idx < len(pixels):
                    top_pixel = pixels[top_idx]
                    bottom_pixel = pixels[bottom_idx] if bottom_idx < len(pixels) else top_pixel

                    # Use Unicode half blocks with ANSI colors
                    # Upper half block with top color as foreground, bottom as background
                    r1, g1, b1 = top_pixel
                    r2, g2, b2 = bottom_pixel

                    # Convert to 256-color mode
                    top_color = 16 + (r1 // 51) * 36 + (g1 // 51) * 6 + (b1 // 51)
                    bottom_color = 16 + (r2 // 51) * 36 + (g2 // 51) * 6 + (b2 // 51)

                    # Use upper half block character
                    row.append(f"\033[38;5;{top_color}m\033[48;5;{bottom_color}m▀\033[0m")

            output.append("".join(row))

        return "\n".join(output)

    except Exception:
        return None
