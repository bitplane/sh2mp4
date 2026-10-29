"""
Screen recording using ffmpeg
"""

import asyncio
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from collections import deque
from contextlib import suppress
from typing import Optional

from .ascii_preview import colored_blocks_preview
from .processes import terminate_process


class Recorder:
    """Handles screen recording with ffmpeg"""

    def __init__(
        self,
        display_name: str,
        width: int,
        height: int,
        fps: int,
        output_path: Path,
        watch: bool = False,
        recording_fps: Optional[int] = None,
        debug: bool = False,
    ):
        self.display_name = display_name
        self.width = width
        self.height = height
        self.fps = fps
        self.recording_fps = recording_fps or fps  # Use recording_fps if provided, otherwise use output fps
        self.output_path = output_path
        self.watch = watch
        self.debug = debug
        self.ffmpeg_process: Optional[asyncio.subprocess.Process] = None
        self.watch_task: Optional[asyncio.Task] = None
        self._stderr_task = None
        self._progress_task = None
        self._errors = deque(maxlen=16)
        self._ready = asyncio.Event()
        self._capture_path = None
        self._content_start = None
        self._content_end = None

    async def start(self) -> None:
        """Start recording the display"""
        # Test X11 connection if in debug mode
        if self.debug:
            test_proc = await asyncio.create_subprocess_exec(
                "xset",
                "-display",
                self.display_name,
                "q",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await test_proc.communicate()
            if test_proc.returncode != 0:
                print(f"DEBUG: X11 connection test failed: {stderr.decode()}", file=sys.stderr)
            else:
                print(f"DEBUG: X11 connection to {self.display_name} OK", file=sys.stderr)

        # Keep potentially large captures alongside the requested output, never in /tmp.
        fd, path = tempfile.mkstemp(prefix=".sh2mp4-", suffix=".mkv", dir=self.output_path.absolute().parent)
        os.close(fd)
        self._capture_path = Path(path)

        cmd = [
            "ffmpeg",
            # Removed -nostdin to allow sending 'q' to stop recording
            "-progress",
            "pipe:1",
            "-stats_period",
            "0.05",
            "-nostats",  # Disable progress statistics
            "-hide_banner",  # Hide copyright banner
            "-loglevel",
            "error" if not self.debug else "info",  # Show more info in debug mode
            "-y",  # Overwrite output file
            "-copyts",
            "-probesize",
            "32",
            "-analyzeduration",
            "0",
            "-f",
            "x11grab",
            "-framerate",
            str(self.recording_fps),
            "-video_size",
            f"{self.width}x{self.height}",
            "-i",
            self.display_name,
        ]

        # Preserve wall-clock X11 timestamps for precise boundary trimming.
        cmd.extend(["-c:v", "ffv1", "-level", "3", "-pix_fmt", "bgr0", str(self._capture_path)])

        env = os.environ.copy()
        env["DISPLAY"] = self.display_name

        if self.debug:
            print(f"DEBUG: ffmpeg command: {' '.join(cmd)}", file=sys.stderr)
        self.ffmpeg_process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdin=asyncio.subprocess.PIPE,  # Allow stdin for sending 'q' to stop
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._stderr_task = asyncio.create_task(self._read_errors())
        self._progress_task = asyncio.create_task(self._read_progress())
        ready = asyncio.create_task(self._ready.wait())
        exited = asyncio.create_task(self.ffmpeg_process.wait())
        try:
            done, _ = await asyncio.wait([ready, exited], timeout=10, return_when=asyncio.FIRST_COMPLETED)
            if exited in done or not done:
                await self.stop()
                raise RuntimeError(self.error_message("FFmpeg failed to start capturing"))
        finally:
            for task in (ready, exited):
                task.cancel()
            await asyncio.gather(ready, exited, return_exceptions=True)

        # Start watch task if requested
        if self.watch:
            self.watch_task = asyncio.create_task(self._watch_display())

    def begin_content(self):
        self._content_start = time.time()

    def end_content(self, cast_duration=None):
        end = time.time()
        speed = self.recording_fps / self.fps
        if cast_duration is not None:
            # Playback ends at the cast's last event. Exclude player startup/import time.
            self._content_start = end - cast_duration / speed
        self._content_end = end + 0.5 / speed

    async def encode(self):
        if self._content_start is None or self._content_end is None:
            raise RuntimeError("Recording boundaries were not set")
        speed = self.recording_fps / self.fps
        filters = f"trim=start={self._content_start}:end={self._content_end},setpts={speed}*(PTS-STARTPTS)"
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-copyts",
            "-i",
            str(self._capture_path),
            "-vf",
            filters,
            "-r",
            str(self.fps),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(self.output_path.absolute()),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await process.communicate()
            if process.returncode:
                raise RuntimeError(f"FFmpeg encoding failed: {stderr.decode(errors='replace').strip()}")
        finally:
            await terminate_process(process)

    async def _read_errors(self):
        while chunk := await self.ffmpeg_process.stderr.read(4096):
            self._errors.append(chunk)
            if self.debug:
                print(chunk.decode(errors="replace"), end="", file=sys.stderr)

    async def _read_progress(self):
        while line := await self.ffmpeg_process.stdout.readline():
            if line.startswith(b"frame=") and int(line.split(b"=", 1)[1]) > 0:
                self._ready.set()

    def error_message(self, message):
        details = b"".join(self._errors).decode(errors="replace").strip()
        return f"{message}: {details}" if details else message

    async def wait_for_failure(self):
        code = await self.ffmpeg_process.wait()
        await self._stderr_task
        raise RuntimeError(self.error_message(f"FFmpeg exited before recording finished (status {code})"))

    async def _watch_display(self) -> None:
        """Show live preview of the display being recorded"""
        temp_dir = tempfile.mkdtemp(prefix="sh2mp4_watch_")
        screenshot_path = os.path.join(temp_dir, "watch.png")

        screenshot_proc = None
        preview_lines = 0  # Track how many lines we printed

        try:
            while True:
                # Take screenshot using ffmpeg
                screenshot_proc = await asyncio.create_subprocess_exec(
                    "ffmpeg",
                    "-nostdin",  # Disable console interactions
                    "-nostats",  # Disable progress statistics
                    "-hide_banner",  # Hide copyright banner
                    "-loglevel",
                    "panic",  # Only fatal errors (even quieter for screenshots)
                    "-f",
                    "x11grab",
                    "-video_size",
                    f"{self.width}x{self.height}",
                    "-i",
                    self.display_name,
                    "-vframes",
                    "1",
                    "-y",
                    screenshot_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )

                await screenshot_proc.wait()

                if screenshot_proc.returncode == 0 and os.path.exists(screenshot_path):
                    # Convert image to colored blocks (back to the good-looking version)
                    preview = colored_blocks_preview(Path(screenshot_path), width=80, height=23)

                    if preview:
                        # Move cursor up to overwrite previous preview
                        if preview_lines > 0:
                            print(f"\033[{preview_lines}A", end="", file=sys.stderr)

                        # Print the preview and status
                        print(preview, file=sys.stderr)
                        print(
                            f"\033[0mRecording: {self.output_path.name}", file=sys.stderr
                        )  # Reset attributes before status

                        # Calculate how many lines we just printed
                        preview_lines = len(preview.split("\n")) + 1  # +1 for status line

                await asyncio.sleep(0.5)  # Update every 500ms

        finally:
            await terminate_process(screenshot_proc)
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("\033[0m", end="", file=sys.stderr)

    async def stop(self) -> int:
        """Finalize the file and return the encoder status; safe to call repeatedly."""
        if self.watch_task:
            self.watch_task.cancel()
            await asyncio.gather(self.watch_task, return_exceptions=True)
        process = self.ffmpeg_process
        if process is None:
            raise RuntimeError("Recording not started")
        if process.returncode is None:
            try:
                process.stdin.write(b"q")
                await process.stdin.drain()
                process.stdin.close()
            except (BrokenPipeError, ConnectionResetError):
                with suppress(ProcessLookupError):
                    process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=30)
        except asyncio.TimeoutError:
            await terminate_process(process)
            raise RuntimeError(self.error_message("FFmpeg timed out finalizing the video"))
        finally:
            await asyncio.gather(
                *(task for task in (self._stderr_task, self._progress_task) if task),
                return_exceptions=True,
            )
        return process.returncode

    async def is_running(self) -> bool:
        """Check if recording is active"""
        return self.ffmpeg_process is not None and self.ffmpeg_process.returncode is None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.ffmpeg_process:
                await self.stop()
        finally:
            if self._capture_path:
                self._capture_path.unlink(missing_ok=True)
