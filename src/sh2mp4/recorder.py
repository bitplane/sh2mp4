"""
Screen recording using ffmpeg
"""

import asyncio
import os
from pathlib import Path
from typing import Optional


class Recorder:
    """Handles screen recording with ffmpeg"""
    
    def __init__(self, display_name: str, width: int, height: int, fps: int, output_path: Path):
        self.display_name = display_name
        self.width = width
        self.height = height
        self.fps = fps
        self.output_path = output_path
        self.ffmpeg_process: Optional[asyncio.subprocess.Process] = None
        
    async def start(self) -> None:
        """Start recording the display"""
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-f", "x11grab",
            "-framerate", str(self.fps),
            "-video_size", f"{self.width}x{self.height}",
            "-i", self.display_name,
            "-c:v", "libx264",
            "-preset", "medium", 
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(self.output_path)
        ]
        
        env = os.environ.copy()
        env["DISPLAY"] = self.display_name
        
        self.ffmpeg_process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
    async def stop(self) -> int:
        """Stop recording and return exit code"""
        if not self.ffmpeg_process:
            raise RuntimeError("Recording not started")
            
        # Send SIGINT to gracefully stop ffmpeg
        self.ffmpeg_process.send_signal(2)  # SIGINT
        
        try:
            # Wait for ffmpeg to finish processing
            return_code = await asyncio.wait_for(self.ffmpeg_process.wait(), timeout=30)
            return return_code
        except asyncio.TimeoutError:
            # Force kill if it doesn't stop gracefully
            self.ffmpeg_process.kill()
            return await self.ffmpeg_process.wait()
            
    async def is_running(self) -> bool:
        """Check if recording is active"""
        return (self.ffmpeg_process is not None and 
                self.ffmpeg_process.returncode is None)
                
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ffmpeg_process and self.ffmpeg_process.returncode is None:
            await self.stop()