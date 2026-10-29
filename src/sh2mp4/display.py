"""
Virtual display management using Xvfb
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from .xserver import is_display_in_use, test_display_connection
from .processes import terminate_process


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
        if self.display_num is not None and await is_display_in_use(self.display_num):
            raise RuntimeError(f"Display :{self.display_num} is already in use")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh2mp4_"))
        await self._start_xvfb(width, height)
        await self._start_openbox()
        for _ in range(100):
            if self.openbox_process.returncode is not None:
                raise RuntimeError(
                    f"Openbox exited during startup ({self.openbox_process.returncode}): "
                    + (self.temp_dir / "openbox.log").read_text()
                )
            proc = await asyncio.create_subprocess_exec(
                "wmctrl",
                "-m",
                env={**os.environ, "DISPLAY": self.display_name},
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                await asyncio.wait_for(proc.wait(), 2)
            finally:
                await terminate_process(proc)
            if proc.returncode == 0:
                break
            await asyncio.sleep(0.05)
        else:
            raise RuntimeError("Openbox did not become ready")
        await self._start_unclutter()
        await asyncio.sleep(0.1)
        if self.unclutter_process.returncode is not None:
            raise RuntimeError("Unclutter exited during startup")

    async def _start_xvfb(self, width: int, height: int) -> None:
        """Let Xvfb atomically allocate a display and report readiness."""
        read_fd, write_fd = os.pipe()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        transport = None
        try:
            transport, _ = await asyncio.get_running_loop().connect_read_pipe(
                lambda: protocol, os.fdopen(read_fd, "rb")
            )
            cmd = ["Xvfb"]
            if self.display_num is not None:
                cmd.append(f":{self.display_num}")
            cmd.extend(
                [
                    "-displayfd",
                    str(write_fd),
                    "-screen",
                    "0",
                    f"{width}x{height}x24",
                    "-noreset",
                    "-nolisten",
                    "tcp",
                    "+extension",
                    "RANDR",
                ]
            )
            self.xvfb_process = await asyncio.create_subprocess_exec(
                *cmd,
                pass_fds=(write_fd,),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            os.close(write_fd)
            write_fd = None
            line = await asyncio.wait_for(reader.readline(), 10)
            if not line.strip().isdigit() or self.xvfb_process.returncode is not None:
                raise RuntimeError("Xvfb failed to start its own display")
            self.display_num = int(line)
            self.display_name = f":{self.display_num}"
            if not await self.is_ready():
                raise RuntimeError("Xvfb display is not accessible")
            print(f"Using display {self.display_name}")
        finally:
            if write_fd is not None:
                os.close(write_fd)
            if transport is not None:
                transport.close()

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

        with (self.temp_dir / "openbox.log").open("wb") as log:
            self.openbox_process = await asyncio.create_subprocess_exec(*cmd, env=env, stdout=log, stderr=log)

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
        try:
            results = await asyncio.gather(
                *(
                    terminate_process(proc)
                    for proc in (self.unclutter_process, self.openbox_process, self.xvfb_process)
                ),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, BaseException):
                    raise result
        finally:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

    async def is_ready(self) -> bool:
        """Check our server's lifetime as well as its connection."""
        if not self.xvfb_process or self.xvfb_process.returncode is not None:
            return False
        connected = await test_display_connection(self.display_name)
        return connected and self.xvfb_process.returncode is None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
