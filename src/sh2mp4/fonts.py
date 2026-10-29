"""Measure the actual xterm font cells used by a recording."""

import os
import subprocess
from dataclasses import dataclass


@dataclass
class FontMetrics:
    width: int
    height: int


def measure_font(font_name: str, font_size: int, display_name=None) -> FontMetrics:
    """Measure a borderless 10 by 10 xterm on the supplied display."""
    env = os.environ.copy()
    if display_name is not None:
        env["DISPLAY"] = display_name
    process = subprocess.Popen(
        [
            "xterm",
            "-fa",
            font_name,
            "-fs",
            str(font_size),
            "-geometry",
            "10x10+0+0",
            "+sb",
            "-b",
            "0",
            "-bw",
            "0",
            "-e",
            "sleep",
            "60",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        search = subprocess.run(
            ["xdotool", "search", "--sync", "--onlyvisible", "--pid", str(process.pid)],
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        window = search.stdout.splitlines()[0]
        geometry = subprocess.run(
            ["xdotool", "getwindowgeometry", "--shell", window],
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        fields = dict(line.split("=", 1) for line in geometry.stdout.splitlines())
        width, height = int(fields["WIDTH"]), int(fields["HEIGHT"])
        if width % 10 or height % 10 or width <= 0 or height <= 0:
            raise RuntimeError(f"Unexpected xterm font geometry: {width}x{height}")
        return FontMetrics(width // 10, height // 10)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def get_font_metrics(font_name: str, font_size: int, display_name=None) -> FontMetrics:
    return measure_font(font_name, font_size, display_name)


def measure_all_fonts(display_name=None):
    fonts = ["Monospace", "DejaVu Sans Mono", "Liberation Mono", "Ubuntu Mono", "Courier New", "Consolas"]
    sizes = [4, 6, 8, 10, 12, 14, 16, 18, 20]
    return {name: {size: measure_font(name, size, display_name) for size in sizes} for name in fonts}


def calculate_window_dimensions(cols: int, lines: int, font_name: str, font_size: int, display_name=None):
    metrics = get_font_metrics(font_name, font_size, display_name)
    width, height = cols * metrics.width, lines * metrics.height
    # At most one pixel of padding, below a cell, for yuv420p's even dimensions.
    return width + width % 2, height + height % 2
