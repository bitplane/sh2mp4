import asyncio
from pathlib import Path

from sh2mp4.recorder import Recorder


async def test_stop_already_exited_encoder():
    recorder = Recorder(":99", 100, 100, 30, Path("unused.mp4"))
    recorder.ffmpeg_process = await asyncio.create_subprocess_exec("false", stdin=asyncio.subprocess.PIPE)
    await recorder.ffmpeg_process.wait()
    assert await recorder.stop() == 1
    assert await recorder.stop() == 1


async def test_encoder_failure_is_not_success(monkeypatch, capsys):
    from unittest.mock import AsyncMock, MagicMock
    from sh2mp4 import __main__ as main
    from sh2mp4.args import parse_args

    display = MagicMock(display_name=":99")
    display.start = AsyncMock()
    display._start_xvfb = AsyncMock()
    display.__aenter__ = AsyncMock(return_value=display)
    display.__aexit__ = AsyncMock(return_value=False)
    terminal = MagicMock()
    terminal.start = AsyncMock()
    terminal.wait_for_completion = AsyncMock(return_value=0)
    terminal.__aenter__ = AsyncMock(return_value=terminal)
    terminal.__aexit__ = AsyncMock(return_value=False)
    recorder = MagicMock()
    recorder.start = AsyncMock()
    recorder.stop = AsyncMock(return_value=1)

    async def pending():
        await asyncio.Future()

    recorder.wait_for_failure = pending
    recorder.error_message = lambda message: message
    recorder.__aenter__ = AsyncMock(return_value=recorder)
    recorder.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(main, "calculate_window_dimensions", lambda *a: (800, 480))
    monkeypatch.setattr(main, "DisplayManager", lambda *a: display)
    monkeypatch.setattr(main, "TerminalManager", lambda *a: terminal)
    monkeypatch.setattr(main, "Recorder", lambda *a, **kw: recorder)
    monkeypatch.setattr(main.asyncio, "sleep", AsyncMock())
    assert await main.record_command(parse_args(["true"])) == 1
    assert "Recording complete:" not in capsys.readouterr().out
