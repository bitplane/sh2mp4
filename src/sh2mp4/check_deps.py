#!/usr/bin/env python3
"""
Check dependencies for sh2mp4
"""

import shutil
import subprocess
import sys


def check_command(cmd: str) -> bool:
    """Check if a command is available in PATH"""
    return shutil.which(cmd) is not None


def check_monospace_fonts() -> bool:
    """Check if monospace fonts are available"""
    try:
        result = subprocess.run(["fc-list"], capture_output=True, text=True, check=True)
        font_list = result.stdout.lower()
        monospace_keywords = ["mono", "courier", "console", "fixed"]
        return any(keyword in font_list for keyword in monospace_keywords)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_required_commands() -> list[str]:
    """Get the runtime tools required by the application"""
    commands = [
        "bash",
        "sleep",
        "xdotool",
        "wmctrl",
        "xprop",
        "xauth",
        "xhost",
        "xdpyinfo",
        "xset",
        "fc-list",
        "ffmpeg",
        "Xvfb",
        "openbox",
        "xterm",
        "unclutter",
        "asciinema",
    ]

    return commands


def check_asciinema_support() -> bool:
    try:
        result = subprocess.run(["asciinema", "play", "--help"], capture_output=True, text=True, check=True, timeout=5)
        return "--out-fmt" in result.stdout and "asciicast" in result.stdout
    except (subprocess.SubprocessError, OSError):
        return False


def check_runtime_dependencies() -> list[str]:
    """Check runtime dependencies and return list of missing commands"""
    required_commands = get_required_commands()
    missing = [cmd for cmd in required_commands if not check_command(cmd)]
    if "asciinema" not in missing and not check_asciinema_support():
        missing.append("asciinema with --out-fmt asciicast support")
    return missing


def main() -> int:
    """Check all dependencies and report status"""
    print("Checking dependencies for sh2mp4...")

    # Required commands
    required_commands = get_required_commands()

    missing = check_runtime_dependencies()
    missing_count = len(missing)
    for cmd in required_commands:
        if cmd in missing:
            print(f"❌ Missing: {cmd}")
        else:
            print(f"✓ Found: {cmd}")
    for dependency in missing:
        if dependency not in required_commands:
            print(f"❌ Missing: {dependency}")

    # Check fonts
    if check_monospace_fonts():
        print("✓ Found monospace font")
    else:
        print("❌ Missing monospace font")
        print("   Please install a monospace font like DejaVu Sans Mono, Liberation Mono, or Courier")
        missing_count += 1

    # Summary
    print()
    if missing_count == 0:
        print("✅ All dependencies satisfied!")
        return 0
    else:
        print(f"⚠️  Missing {missing_count} dependencies.")
        print("Please install missing dependencies before using sh2mp4")
        return 1


if __name__ == "__main__":
    sys.exit(main())
