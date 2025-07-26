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


def check_locale() -> bool:
    """Check if en_US.UTF-8 locale is available"""
    try:
        result = subprocess.run(["locale", "-a"], capture_output=True, text=True, check=True)
        locales = result.stdout.lower()
        return "en_us.utf8" in locales or "en_us.utf-8" in locales
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_monospace_fonts() -> bool:
    """Check if monospace fonts are available"""
    try:
        result = subprocess.run(["fc-list"], capture_output=True, text=True, check=True)
        font_list = result.stdout.lower()
        monospace_keywords = ["mono", "courier", "console", "fixed"]
        return any(keyword in font_list for keyword in monospace_keywords)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_required_commands(cast_file_mode: bool = False) -> list[str]:
    """Get list of required commands based on mode"""
    commands = ["xdotool", "wmctrl", "ffmpeg", "Xvfb", "openbox", "xterm", "unclutter"]

    if cast_file_mode:
        commands.append("asciinema")

    return commands


def check_runtime_dependencies(cast_file_mode: bool = False) -> list[str]:
    """Check runtime dependencies and return list of missing commands"""
    required_commands = get_required_commands(cast_file_mode)
    return [cmd for cmd in required_commands if not check_command(cmd)]


def main() -> int:
    """Check all dependencies and report status"""
    print("Checking dependencies for sh2mp4...")

    # Required commands
    required_commands = get_required_commands()

    # Optional commands (not required for core functionality)
    optional_commands = ["asciinema"]

    missing_count = 0

    # Check required commands
    for cmd in required_commands:
        if check_command(cmd):
            print(f"✓ Found: {cmd}")
        else:
            print(f"❌ Missing: {cmd}")
            missing_count += 1

    # Check optional commands (but don't count asciinema as optional if it's already required)
    for cmd in optional_commands:
        if cmd not in required_commands:
            if check_command(cmd):
                print(f"✓ Found: {cmd} (optional)")
            else:
                print(f"⚠️  Missing: {cmd} (optional)")

    # Check locale
    if check_locale():
        print("✓ Found locale: en_US.UTF-8")
    else:
        print("❌ Missing locale: en_US.UTF-8")
        print("   You may need to run: sudo locale-gen en_US.UTF-8")
        missing_count += 1

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
