"""
Terminal (xterm) management for command execution
"""

import asyncio
import os
import shutil
import shlex
import tempfile
from pathlib import Path
from typing import Optional

from .themes import Theme
from .processes import terminate_process


class TerminalManager:
    """Manages an xterm instance for command execution"""

    def __init__(
        self,
        display_name: str,
        theme: Theme,
        font_name: str,
        font_size: int,
        cols: int,
        lines: int,
        width: int,
        height: int,
    ):
        self.display_name = display_name
        self.theme = theme
        self.font_name = font_name
        self.font_size = font_size
        self.cols = cols
        self.lines = lines
        self.width = width
        self.height = height
        self.xterm_process: Optional[asyncio.subprocess.Process] = None
        self.temp_dir: Optional[Path] = None
        self.window_id: Optional[str] = None

    async def start(self, command: str) -> None:
        """Start xterm and execute the command"""
        # Create temporary directory for scripts
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sh2mp4_terminal_"))

        # Create command script
        command_script = self._create_command_script(command)

        # Start xterm
        await self._start_xterm(command_script)

        # Wait for window to appear and configure it
        await self._wait_for_window()
        await self._configure_window()

    def _create_command_script(self, command: str) -> Path:
        """Create a script file with the command to execute"""
        script_path = self.temp_dir / "command.sh"
        sync_file = self.temp_dir / "recorder_ready"

        payload = self.temp_dir / "payload.sh"
        payload.write_text(command + "\n")
        script_content = f"""#!/usr/bin/env bash
while [ ! -f {shlex.quote(str(sync_file))} ]; do
    sleep 0.01
done
bash {shlex.quote(str(payload))}
status=$?
# Keep both successful and failed output visible until the recorder stops.
printf '%s' "$status" > {shlex.quote(str(self.temp_dir / "exit_status"))}
while :; do sleep 0.1; done
"""

        script_path.write_text(script_content)
        script_path.chmod(0o755)

        return script_path

    def signal_recorder_ready(self) -> None:
        """Signal that the recorder is ready and command can proceed"""
        if self.temp_dir:
            sync_file = self.temp_dir / "recorder_ready"
            sync_file.touch()

    async def _start_xterm(self, script_path: Path) -> None:
        """Start the xterm process"""
        cmd = [
            "xterm",
            "-fa",
            self.font_name,
            "-fs",
            str(self.font_size),
            "-geometry",
            f"{self.cols}x{self.lines}",
            "-T",
            "sh2mp4_recording",
            "+sb",  # No scrollbar
            "-b",
            "0",  # No border
            "-bw",
            "0",  # No border width
            "+maximized",
        ]

        # Add theme arguments before -e option (must be last)
        cmd.extend(self.theme.xterm_args)

        # Add -e option last (as required by xterm)
        cmd.extend(["-e", str(script_path)])

        env = os.environ.copy()
        env["DISPLAY"] = self.display_name

        self.xterm_process = await asyncio.create_subprocess_exec(
            *cmd, env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )

    async def _wait_for_window(self) -> None:
        """Wait for the xterm window to appear"""
        for i in range(50):  # Try for up to 5 seconds
            if self.xterm_process.returncode is not None:
                raise RuntimeError("Xterm exited during startup")
            try:
                # Find xterm window
                proc = await asyncio.create_subprocess_exec(
                    "xdotool",
                    "search",
                    "--onlyvisible",
                    "--class",
                    "xterm",
                    env={**os.environ, "DISPLAY": self.display_name},
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await proc.communicate()

                if proc.returncode == 0 and stdout.strip():
                    window_ids = stdout.decode().strip().split("\n")
                    if window_ids and window_ids[0]:
                        self.window_id = window_ids[0]
                        print(f"Found xterm window ID: {self.window_id}")
                        return

            except Exception as e:
                if i % 10 == 0:  # Print debug info every second
                    print(f"Waiting for xterm window... (attempt {i + 1}/50): {e}")

            await asyncio.sleep(0.1)

        raise RuntimeError("Failed to find xterm window")

    async def _configure_window(self) -> None:
        """Configure the window (size, position, decorations)"""
        if not self.window_id:
            return

        env = {**os.environ, "DISPLAY": self.display_name}

        commands = [
            [
                "xprop",
                "-id",
                self.window_id,
                "-f",
                "_MOTIF_WM_HINTS",
                "32c",
                "-set",
                "_MOTIF_WM_HINTS",
                "0x2, 0x0, 0x0, 0x0, 0x0",
            ],
            ["wmctrl", "-ir", self.window_id, "-e", f"0,0,0,{self.width},{self.height}"],
            ["wmctrl", "-ir", self.window_id, "-b", "add,fullscreen"],
        ]
        for cmd in commands:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                _, stderr = await asyncio.wait_for(proc.communicate(), 5)
                if proc.returncode:
                    raise RuntimeError(f"{cmd[0]} failed: {stderr.decode(errors='replace')}")
            finally:
                await terminate_process(proc)

    async def wait_for_completion(self) -> int:
        """Wait for the terminal/command to complete and return exit code"""
        if not self.xterm_process:
            raise RuntimeError("Terminal not started")

        status_file = self.temp_dir / "exit_status"
        while self.xterm_process.returncode is None:
            if status_file.exists():
                status = status_file.read_text().strip()
                if status:
                    return int(status)
            await asyncio.sleep(0.01)
        raise RuntimeError(f"Xterm exited before reporting command status ({self.xterm_process.returncode})")

    async def is_running(self) -> bool:
        """Check if the terminal is still running"""
        return self.xterm_process is not None and self.xterm_process.returncode is None

    async def stop(self) -> None:
        """Stop the terminal and clean up"""
        try:
            await terminate_process(self.xterm_process)
        finally:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
