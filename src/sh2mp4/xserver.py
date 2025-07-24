"""
X server management utilities
"""

import asyncio
from pathlib import Path
from typing import List, Optional


class XServerInfo:
    """Information about an X server"""

    def __init__(
        self,
        display_num: int,
        socket_path: Optional[Path] = None,
        lock_path: Optional[Path] = None,
        pid: Optional[int] = None,
    ):
        self.display_num = display_num
        self.display_name = f":{display_num}"
        self.socket_path = socket_path
        self.lock_path = lock_path
        self.pid = pid

    def __repr__(self):
        return f"XServerInfo(display={self.display_name}, pid={self.pid})"


async def find_available_display() -> int:
    """Find the next available X display number"""
    for display_num in range(99, 200):  # Start at 99, go up to 199
        if not await is_display_in_use(display_num):
            return display_num

    raise RuntimeError("No available X display numbers found")


async def is_display_in_use(display_num: int) -> bool:
    """Check if a display number is already in use"""
    # Check for X11 lock file
    lock_file = Path(f"/tmp/.X{display_num}-lock")
    if lock_file.exists():
        return True

    # Check for X11 socket
    socket_path = Path(f"/tmp/.X11-unix/X{display_num}")
    if socket_path.exists():
        return True

    # Try to connect to see if something is listening
    try:
        proc = await asyncio.create_subprocess_exec(
            "xdpyinfo",
            "-display",
            f":{display_num}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        # xdpyinfo not available, assume not in use
        return False


async def list_running_xservers() -> List[XServerInfo]:
    """List all currently running X servers"""
    servers = []

    # Look for X11 sockets in /tmp/.X11-unix/
    x11_unix_dir = Path("/tmp/.X11-unix")
    if x11_unix_dir.exists():
        for socket_file in x11_unix_dir.glob("X*"):
            try:
                display_num = int(socket_file.name[1:])  # Remove 'X' prefix

                # Get lock file info
                lock_file = Path(f"/tmp/.X{display_num}-lock")
                pid = None
                if lock_file.exists():
                    try:
                        pid_text = lock_file.read_text().strip()
                        pid = int(pid_text.split()[0])  # First number is the PID
                    except (ValueError, IndexError):
                        pass

                servers.append(
                    XServerInfo(
                        display_num=display_num,
                        socket_path=socket_file,
                        lock_path=lock_file if lock_file.exists() else None,
                        pid=pid,
                    )
                )

            except ValueError:
                # Not a valid display number
                continue

    # Sort by display number
    servers.sort(key=lambda x: x.display_num)
    return servers


async def get_newest_xserver() -> Optional[XServerInfo]:
    """Get the most recently started X server"""
    servers = await list_running_xservers()

    if not servers:
        return None

    # Find the server with the highest display number (most recent)
    return max(servers, key=lambda x: x.display_num)


async def test_display_connection(display_name: str) -> bool:
    """Test if we can connect to a display"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "xdpyinfo", "-display", display_name, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        # xdpyinfo not available, try a different approach
        try:
            # Try to list windows
            proc = await asyncio.create_subprocess_exec(
                "xwininfo",
                "-display",
                display_name,
                "-root",
                "-tree",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            # No X11 tools available, assume it works
            return True
