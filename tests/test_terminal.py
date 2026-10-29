import asyncio

from sh2mp4.terminal import TerminalManager
from sh2mp4.themes import get_theme


async def test_failed_command_status_and_output_retained(tmp_path):
    terminal = TerminalManager(":99", get_theme("dark"), "DejaVu Sans Mono", 12, 80, 24, 820, 496)
    terminal.temp_dir = tmp_path / "terminal"
    terminal.temp_dir.mkdir()
    script = terminal._create_command_script("echo failed; exit 7")
    terminal.xterm_process = await asyncio.create_subprocess_exec("bash", str(script))
    try:
        terminal.signal_recorder_ready()
        assert await asyncio.wait_for(terminal.wait_for_completion(), 2) == 7
        assert terminal.xterm_process.returncode is None
    finally:
        await terminal.stop()


async def test_normal_pipeline_uses_bash_exit_status(tmp_path):
    terminal = TerminalManager(":99", get_theme("dark"), "DejaVu Sans Mono", 12, 80, 24, 820, 496)
    terminal.temp_dir = tmp_path / "terminal"
    terminal.temp_dir.mkdir()
    script = terminal._create_command_script("yes | head -5")
    terminal.xterm_process = await asyncio.create_subprocess_exec(
        "bash", str(script), stdout=asyncio.subprocess.DEVNULL
    )
    try:
        terminal.signal_recorder_ready()
        assert await asyncio.wait_for(terminal.wait_for_completion(), 2) == 0
    finally:
        await terminal.stop()
