"""
Screen recording using ffmpeg
"""

import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional


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

        cmd = [
            "ffmpeg",
            # Removed -nostdin to allow sending 'q' to stop recording
            "-nostats",  # Disable progress statistics
            "-hide_banner",  # Hide copyright banner
            "-loglevel",
            "error" if not self.debug else "info",  # Show more info in debug mode
            "-y",  # Overwrite output file
            "-f",
            "x11grab",
            "-framerate",
            str(self.recording_fps),
            "-video_size",
            f"{self.width}x{self.height}",
            "-i",
            self.display_name,
        ]

        # If recording at higher fps than output fps, add filter to slow down to real-time
        if self.recording_fps != self.fps:
            speed_factor = self.fps / self.recording_fps
            cmd.extend(["-vf", f"setpts={1/speed_factor}*PTS", "-r", str(self.fps)])

        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                str(self.output_path),
            ]
        )

        env = os.environ.copy()
        env["DISPLAY"] = self.display_name

        if self.debug:
            print(f"DEBUG: ffmpeg command: {' '.join(cmd)}", file=sys.stderr)
            stderr_dest = None
            stdout_dest = None
        else:
            stderr_dest = asyncio.subprocess.DEVNULL
            stdout_dest = asyncio.subprocess.DEVNULL

        self.ffmpeg_process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdin=asyncio.subprocess.PIPE,  # Allow stdin for sending 'q' to stop
            stdout=stdout_dest,
            stderr=stderr_dest,
        )

        # Start watch task if requested
        if self.watch:
            self.watch_task = asyncio.create_task(self._watch_display())

    async def _watch_display(self) -> None:
        """Show live preview of the display being recorded"""
        from .ascii_preview import colored_blocks_preview

        temp_dir = tempfile.mkdtemp(prefix="sh2mp4_watch_")
        screenshot_path = os.path.join(temp_dir, "watch.png")

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

        except asyncio.CancelledError:
            # Reset terminal attributes on cancellation
            print("\033[0m", end="", file=sys.stderr)  # Reset all attributes

            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
        finally:
            # Always reset terminal attributes on exit
            print("\033[0m", end="", file=sys.stderr)  # Reset all attributes

    async def stop(self) -> int:
        """Stop recording and return exit code"""
        if not self.ffmpeg_process:
            raise RuntimeError("Recording not started")

        # Cancel watch task if running
        if self.watch_task and not self.watch_task.done():
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass

        # Send 'q' to stdin to gracefully stop ffmpeg
        if self.debug:
            print("DEBUG: Sending 'q' to ffmpeg stdin...", file=sys.stderr)
        try:
            self.ffmpeg_process.stdin.write(b"q")
            await self.ffmpeg_process.stdin.drain()
            self.ffmpeg_process.stdin.close()
        except Exception as e:
            if self.debug:
                print(f"DEBUG: Failed to send 'q': {e}", file=sys.stderr)
            # Fall back to SIGTERM
            self.ffmpeg_process.terminate()

        try:
            # Wait for ffmpeg to finish processing
            if self.debug:
                print("DEBUG: Waiting for ffmpeg to terminate...", file=sys.stderr)
            return_code = await asyncio.wait_for(self.ffmpeg_process.wait(), timeout=5)
            if self.debug:
                print(f"DEBUG: ffmpeg terminated with code {return_code}", file=sys.stderr)
            return return_code
        except asyncio.TimeoutError:
            if self.debug:
                print("DEBUG: ffmpeg timeout, force killing...", file=sys.stderr)
            # Force kill if it doesn't stop gracefully
            self.ffmpeg_process.kill()
            return_code = await self.ffmpeg_process.wait()
            if self.debug:
                print(f"DEBUG: ffmpeg killed with code {return_code}", file=sys.stderr)
            return return_code

    async def is_running(self) -> bool:
        """Check if recording is active"""
        return self.ffmpeg_process is not None and self.ffmpeg_process.returncode is None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ffmpeg_process and self.ffmpeg_process.returncode is None:
            await self.stop()
