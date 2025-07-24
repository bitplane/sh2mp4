"""
Virtual display management using Xvfb
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Optional

from .xserver import find_available_display


class DisplayManager:
    """Manages a virtual X display using Xvfb"""

    def __init__(self, display_num: Optional[int] = None):
        self.display_num = display_num  # Will be set in start() if None
        self.display_name: Optional[str] = None
        self.xvfb_process: Optional[asyncio.subprocess.Process] = None
        self.openbox_process: Optional[asyncio.subprocess.Process] = None
        self.unclutter_process: Optional[asyncio.subprocess.Process] = None
        self.temp_dir: Optional[Path] = None

    async def start(self, width: int, height: int) -> None:
        """Start the virtual display and window manager"""
        # Find available display if not specified
        if self.display_num is None:
            self.display_num = await find_available_display()

        self.display_name = f":{self.display_num}"
        print(f"Using display {self.display_name}")

        # Create temporary directory for configs
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh2mp4_"))

        # Start Xvfb
        await self._start_xvfb(width, height)

        # Wait a bit for Xvfb to initialize
        await asyncio.sleep(1)

        # Start window manager
        await self._start_openbox()

        # Wait for window manager to initialize
        await asyncio.sleep(1)

        # Start unclutter to hide mouse cursor
        await self._start_unclutter()

        # Wait for unclutter to initialize
        await asyncio.sleep(0.5)

    async def _start_xvfb(self, width: int, height: int) -> None:
        """Start the Xvfb virtual display server"""
        cmd = ["Xvfb", self.display_name, "-screen", "0", f"{width}x{height}x24", "+extension", "RANDR"]

        self.xvfb_process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )

        # Set the DISPLAY environment variable
        os.environ["DISPLAY"] = self.display_name

    async def _start_openbox(self) -> None:
        """Start the Openbox window manager"""
        # Create openbox config directory
        config_dir = self.temp_dir / "openbox"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create openbox configuration
        config_file = config_dir / "rc.xml"
        config_content = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <applications>
    <application class="*">
      <decor>no</decor>
      <maximized>yes</maximized>
    </application>
  </applications>
</openbox_config>"""

        config_file.write_text(config_content)

        # Start openbox
        cmd = ["openbox", "--config-file", str(config_file)]

        env = os.environ.copy()
        env["DISPLAY"] = self.display_name

        self.openbox_process = await asyncio.create_subprocess_exec(
            *cmd, env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )

    async def _start_unclutter(self) -> None:
        """Start unclutter to hide the mouse cursor"""
        cmd = ["unclutter", "-idle", "0"]

        env = os.environ.copy()
        env["DISPLAY"] = self.display_name

        self.unclutter_process = await asyncio.create_subprocess_exec(
            *cmd, env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )

    async def stop(self) -> None:
        """Stop the display and clean up"""
        # Stop unclutter
        if self.unclutter_process:
            try:
                self.unclutter_process.terminate()
                await asyncio.wait_for(self.unclutter_process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.unclutter_process.kill()
                await self.unclutter_process.wait()

        # Stop openbox
        if self.openbox_process:
            try:
                self.openbox_process.terminate()
                await asyncio.wait_for(self.openbox_process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.openbox_process.kill()
                await self.openbox_process.wait()

        # Stop Xvfb
        if self.xvfb_process:
            try:
                self.xvfb_process.terminate()
                await asyncio.wait_for(self.xvfb_process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.xvfb_process.kill()
                await self.xvfb_process.wait()

        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            import shutil

            shutil.rmtree(self.temp_dir)

        # Clean DISPLAY env var
        if "DISPLAY" in os.environ and os.environ["DISPLAY"] == self.display_name:
            del os.environ["DISPLAY"]

    async def is_ready(self) -> bool:
        """Check if the display is ready for use"""
        if not self.xvfb_process or self.xvfb_process.returncode is not None:
            return False

        # Try to connect to the display
        try:
            proc = await asyncio.create_subprocess_exec(
                "xdpyinfo",
                "-display",
                self.display_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            # xdpyinfo not available, assume it's working
            return True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
