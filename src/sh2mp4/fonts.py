"""
Font handling and character dimension calculation
"""

import tkinter as tk
from tkinter import font as tkfont
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class FontMetrics:
    """Character dimensions for a specific font and size"""

    width: int
    height: int


# Pre-measured font dimensions for DejaVu Sans Mono
# Format: {font_size: (width, height)}
DEJAVU_SANS_MONO_METRICS = {
    4: FontMetrics(3, 7),
    6: FontMetrics(5, 10),
    8: FontMetrics(6, 13),
    10: FontMetrics(8, 17),
    12: FontMetrics(10, 19),
    14: FontMetrics(11, 23),
    16: FontMetrics(13, 26),
    18: FontMetrics(14, 29),
    20: FontMetrics(16, 32),
}


def get_font_metrics(font_name: str, font_size: int) -> FontMetrics:
    """
    Get character dimensions for a font and size.
    Falls back to pre-measured values for DejaVu Sans Mono.
    """
    # Use pre-measured values for DejaVu Sans Mono
    if font_name == "DejaVu Sans Mono" and font_size in DEJAVU_SANS_MONO_METRICS:
        return DEJAVU_SANS_MONO_METRICS[font_size]

    # Try to measure dynamically
    try:
        return measure_font(font_name, font_size)
    except Exception:
        # Fall back to size 12 DejaVu Sans Mono metrics
        return DEJAVU_SANS_MONO_METRICS.get(12, FontMetrics(10, 19))


def measure_font(font_name: str, font_size: int) -> FontMetrics:
    """Dynamically measure font character dimensions using tkinter"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    try:
        font = tkfont.Font(family=font_name, size=font_size)
        width = font.measure("M")  # Width of capital M
        height = font.metrics("linespace")  # Line height
        return FontMetrics(width, height)
    finally:
        root.destroy()


def measure_all_fonts() -> Dict[str, Dict[int, FontMetrics]]:
    """Measure all common monospace fonts at various sizes"""
    fonts = [
        "Monospace",
        "DejaVu Sans Mono",
        "Liberation Mono",
        "Ubuntu Mono",
        "Courier New",
        "Consolas",
    ]

    sizes = [4, 6, 8, 10, 12, 14, 16, 18, 20]

    results = {}

    for font_name in fonts:
        results[font_name] = {}
        for size in sizes:
            try:
                metrics = measure_font(font_name, size)
                results[font_name][size] = metrics
            except Exception:
                continue

    return results


def calculate_window_dimensions(cols: int, lines: int, font_name: str, font_size: int) -> Tuple[int, int]:
    """Calculate pixel dimensions for terminal window with padding for xterm margins"""
    metrics = get_font_metrics(font_name, font_size)

    width = cols * metrics.width
    height = lines * metrics.height

    # Add padding for xterm internal margins and window manager overhead
    HORIZONTAL_PADDING = 20  # 10 pixels per side for margins

    # Add one full character height as grace space to prevent scrolling
    # if command output wraps or produces an extra line
    height += metrics.height  # One extra line of grace

    width += HORIZONTAL_PADDING
    height += HORIZONTAL_PADDING  # Keep some vertical padding for window manager

    # Ensure dimensions are even (required for H.264 encoding)
    width += width % 2
    height += height % 2

    return width, height
