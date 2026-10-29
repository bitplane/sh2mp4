"""Measure the actual xterm font cells used by a recording."""

import os
import asyncio
from dataclasses import dataclass

from .processes import terminate_process


@dataclass
class FontMetrics:
    width: int
    height: int


async def measure_font(font_name: str, font_size: int, display_name=None) -> FontMetrics:
    """Measure a borderless 10 by 10 xterm on the supplied display."""
    env = os.environ.copy()
    if display_name is not None:
        env["DISPLAY"] = display_name
    process = await asyncio.create_subprocess_exec(
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
        env=env,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        search = await _run_xdotool("search", "--sync", "--onlyvisible", "--pid", str(process.pid), env=env)
        window = search.splitlines()[0]
        geometry = await _run_xdotool("getwindowgeometry", "--shell", window, env=env)
        fields = dict(line.split("=", 1) for line in geometry.splitlines())
        width, height = int(fields["WIDTH"]), int(fields["HEIGHT"])
        if width % 10 or height % 10 or width <= 0 or height <= 0:
            raise RuntimeError(f"Unexpected xterm font geometry: {width}x{height}")
        return FontMetrics(width // 10, height // 10)
    finally:
        await terminate_process(process)


async def _run_xdotool(*args, env):
    process = await asyncio.create_subprocess_exec(
        "xdotool",
        *args,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), 5)
        if process.returncode:
            raise RuntimeError(f"Font measurement failed: {stderr.decode(errors='replace')}")
        return stdout.decode()
    except asyncio.TimeoutError as e:
        raise RuntimeError("Timed out measuring xterm font cells") from e
    finally:
        await terminate_process(process)


async def get_font_metrics(font_name: str, font_size: int, display_name=None) -> FontMetrics:
    return await measure_font(font_name, font_size, display_name)


async def measure_all_fonts(display_name=None):
    fonts = ["Monospace", "DejaVu Sans Mono", "Liberation Mono", "Ubuntu Mono", "Courier New", "Consolas"]
    sizes = [4, 6, 8, 10, 12, 14, 16, 18, 20]
    return {name: {size: await measure_font(name, size, display_name) for size in sizes} for name in fonts}


async def calculate_window_dimensions(cols: int, lines: int, font_name: str, font_size: int, display_name=None):
    metrics = await get_font_metrics(font_name, font_size, display_name)
    width, height = cols * metrics.width, lines * metrics.height
    # At most one pixel of padding, below a cell, for yuv420p's even dimensions.
    return width + width % 2, height + height % 2
