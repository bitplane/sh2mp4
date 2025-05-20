#!/usr/bin/env python3
import tkinter as tk
from tkinter import font as tkfont


def measure_monospace_fonts():
    """Measure the pixel dimensions of common monospace fonts at different sizes."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # List of common monospace fonts to test
    monospace_fonts = [
        "Monospace",
        "DejaVu Sans Mono",
        "Liberation Mono",
        "Ubuntu Mono",
        "Courier New",
        "Consolas",
    ]

    # Font sizes to test
    font_sizes = [4, 6, 8, 10, 12, 14, 16, 18, 20]

    for font_name in monospace_fonts:
        try:
            for size in font_sizes:
                # Try to create the font
                try:
                    f = tkfont.Font(family=font_name, size=size)

                    # Measure dimensions
                    width = f.measure("M")  # Width of capital M
                    height = f.metrics("linespace")  # Line height

                    print(f"{font_name} {size} {width}x{height}")
                except Exception as e:
                    pass
        except Exception as e:
            print(f"| {font_name:<11} | Error: {str(e)} |")

    root.destroy()


if __name__ == "__main__":
    measure_monospace_fonts()
