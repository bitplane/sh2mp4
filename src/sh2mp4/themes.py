"""
Terminal color themes for sh2mp4
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """Represents a terminal color theme"""

    name: str
    background: str
    foreground: str
    colors: Dict[int, str]  # Colors 0-15

    @property
    def xterm_args(self) -> list[str]:
        """Generate xterm arguments for this theme"""
        args = [
            "-bg",
            self.background,
            "-fg",
            self.foreground,
        ]

        for i, color in self.colors.items():
            args.extend(["-xrm", f"XTerm*color{i}: {color}"])

        return args


# Theme definitions
THEMES = {
    "sh2mp4": Theme(
        name="sh2mp4",
        background="#000000",
        foreground="#ffffff",
        colors={
            0: "#2e3436",  # Black
            1: "#cc0000",  # Red
            2: "#4e9a06",  # Green
            3: "#c4a000",  # Yellow
            4: "#346da4",  # Blue
            5: "#75507b",  # Magenta
            6: "#06989a",  # Cyan
            7: "#d3d7cf",  # Light gray
            8: "#555753",  # Dark gray
            9: "#ef2929",  # Bright red
            10: "#8ae234",  # Bright green
            11: "#fce94f",  # Bright yellow
            12: "#729fcf",  # Bright blue
            13: "#ad7fa8",  # Bright magenta
            14: "#34e2e2",  # Bright cyan
            15: "#eeeeec",  # White
        },
    ),
    "tango": Theme(
        name="tango",
        background="#2e3436",
        foreground="#d3d7cf",
        colors={
            0: "#2e3436",  # Black
            1: "#cc0000",  # Red
            2: "#4e9a06",  # Green
            3: "#c4a000",  # Yellow
            4: "#3465a4",  # Blue
            5: "#75507b",  # Magenta
            6: "#06989a",  # Cyan
            7: "#d3d7cf",  # Light gray
            8: "#555753",  # Dark gray
            9: "#ef2929",  # Bright red
            10: "#8ae234",  # Bright green
            11: "#fce94f",  # Bright yellow
            12: "#729fcf",  # Bright blue
            13: "#ad7fa8",  # Bright magenta
            14: "#34e2e2",  # Bright cyan
            15: "#eeeeec",  # White
        },
    ),
    "dark": Theme(
        name="dark",
        background="#000000",
        foreground="#ffffff",
        colors={
            0: "#000000",  # Black
            1: "#cd0000",  # Red
            2: "#00cd00",  # Green
            3: "#cdcd00",  # Yellow
            4: "#0000ee",  # Blue
            5: "#cd00cd",  # Magenta
            6: "#00cdcd",  # Cyan
            7: "#e5e5e5",  # Light gray
            8: "#7f7f7f",  # Dark gray
            9: "#ff0000",  # Bright red
            10: "#00ff00",  # Bright green
            11: "#ffff00",  # Bright yellow
            12: "#5c5cff",  # Bright blue
            13: "#ff00ff",  # Bright magenta
            14: "#00ffff",  # Bright cyan
            15: "#ffffff",  # White
        },
    ),
    "light": Theme(
        name="light",
        background="#ffffff",
        foreground="#000000",
        colors={
            0: "#000000",  # Black
            1: "#990000",  # Red
            2: "#006600",  # Green
            3: "#999900",  # Yellow
            4: "#0000cc",  # Blue
            5: "#990099",  # Magenta
            6: "#009999",  # Cyan
            7: "#cccccc",  # Light gray
            8: "#666666",  # Dark gray
            9: "#cc0000",  # Bright red
            10: "#00aa00",  # Bright green
            11: "#cccc00",  # Bright yellow
            12: "#0000ff",  # Bright blue
            13: "#cc00cc",  # Bright magenta
            14: "#00cccc",  # Bright cyan
            15: "#ffffff",  # White
        },
    ),
    "solarized-dark": Theme(
        name="solarized-dark",
        background="#002b36",
        foreground="#839496",
        colors={
            0: "#073642",  # Black
            1: "#dc322f",  # Red
            2: "#859900",  # Green
            3: "#b58900",  # Yellow
            4: "#268bd2",  # Blue
            5: "#d33682",  # Magenta
            6: "#2aa198",  # Cyan
            7: "#eee8d5",  # Light gray
            8: "#002b36",  # Dark gray
            9: "#cb4b16",  # Bright red
            10: "#586e75",  # Bright green
            11: "#657b83",  # Bright yellow
            12: "#839496",  # Bright blue
            13: "#6c71c4",  # Bright magenta
            14: "#93a1a1",  # Bright cyan
            15: "#fdf6e3",  # White
        },
    ),
}


def get_theme(name: str) -> Theme:
    """Get a theme by name, falling back to default"""
    return THEMES.get(name, THEMES["sh2mp4"])


def list_themes() -> list[str]:
    """List available theme names"""
    return list(THEMES.keys())
