"""
Asciinema cast file handling and optimization
"""

import json
from pathlib import Path
from typing import NamedTuple


class CastConfig(NamedTuple):
    """Configuration for recording a cast file"""

    cols: int
    lines: int
    command: str
    playback_speed: float = 1.0
    recording_fps: int = 30


def get_cast_dimensions(cast_file: Path) -> tuple[int, int]:
    """Get optimal dimensions for cast file recording"""
    try:
        max_width, max_height = _find_max_cast_dimensions(cast_file)
        print(f"Cast file dimensions: {max_width}x{max_height} characters (optimized)")
        return max_width, max_height
    except Exception as e:
        # Fallback to header dimensions
        try:
            width, height = _parse_cast_header(cast_file)
            print(f"Cast file dimensions: {width}x{height} characters (from header)")
            return width, height
        except Exception:
            raise ValueError(f"Failed to parse cast file: {e}")


def get_cast_command(cast_file: Path, playback_speed: float = 1.0) -> str:
    """Get the command to play back a cast file"""
    speed_arg = f" -s {playback_speed}" if playback_speed != 1.0 else ""
    return f'bash -c "asciinema play -i 1{speed_arg} \\"{cast_file.absolute()}\\""'


def get_cast_config(cast_file: Path, playback_speed: float = 1.0, base_fps: int = 30) -> CastConfig:
    """Get complete configuration for recording a cast file"""
    cols, lines = get_cast_dimensions(cast_file)
    command = get_cast_command(cast_file, playback_speed)
    recording_fps = int(base_fps * playback_speed)

    return CastConfig(
        cols=cols, lines=lines, command=command, playback_speed=playback_speed, recording_fps=recording_fps
    )


def _parse_cast_header(cast_file: Path) -> tuple[int, int]:
    """Parse the asciinema cast file header to get initial dimensions"""
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
        raise ValueError(f"Failed to parse cast file header: {e}")


def _find_max_cast_dimensions(cast_file: Path) -> tuple[int, int]:
    """Scan cast file for window resize events to find maximum dimensions"""
    max_width, max_height = _parse_cast_header(cast_file)

    try:
        with cast_file.open() as f:
            # Skip header line
            f.readline()

            # Scan through all event lines looking for resize sequences
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    # Check if this is a resize event (type "r")
                    if len(event) >= 3 and event[1] == "r":
                        # Asciinema resize format: [timestamp, "r", "WIDTHxHEIGHT"]
                        resize_data = event[2]
                        if "x" in resize_data:
                            try:
                                width_str, height_str = resize_data.split("x", 1)
                                width = int(width_str)
                                height = int(height_str)
                                max_width = max(max_width, width)
                                max_height = max(max_height, height)
                            except (ValueError, IndexError):
                                continue

                except (json.JSONDecodeError, IndexError):
                    # Skip malformed lines
                    continue

    except Exception:
        # If scanning fails, fall back to header dimensions
        pass

    return max_width, max_height
