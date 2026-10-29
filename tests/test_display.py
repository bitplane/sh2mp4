import asyncio
import os
from unittest.mock import AsyncMock

import pytest

from sh2mp4.display import DisplayManager


async def test_cleanup_exited_helper_and_restore_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("DISPLAY", ":original")
    display = DisplayManager()
    display.temp_dir = tmp_path / "display"
    display.temp_dir.mkdir()
    display.unclutter_process = await asyncio.create_subprocess_exec("true")
    await display.unclutter_process.wait()
    display.xvfb_process = await asyncio.create_subprocess_exec("sleep", "60")
    await display.stop()
    await display.stop()
    assert display.xvfb_process.returncode is not None
    assert not display.temp_dir.exists()
    assert os.environ["DISPLAY"] == ":original"


async def test_reject_occupied_display(monkeypatch):
    monkeypatch.setattr("sh2mp4.display.is_display_in_use", AsyncMock(return_value=True))
    spawn = AsyncMock()
    monkeypatch.setattr("sh2mp4.display.asyncio.create_subprocess_exec", spawn)
    async with DisplayManager(42) as display:
        with pytest.raises(RuntimeError, match="already in use"):
            await display.start(100, 100)
    spawn.assert_not_called()
