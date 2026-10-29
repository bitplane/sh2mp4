"""Opt-in real X11/FFmpeg checks: SH2MP4_INTEGRATION=1 pytest tests/test_integration.py."""

import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("SH2MP4_INTEGRATION") != "1", reason="requires runtime X11 tools")


def run(*args):
    return subprocess.run([sys.executable, "-m", "sh2mp4", *args], capture_output=True, text=True, timeout=45)


@pytest.mark.parametrize("speed", [None, "2x", "4x", "8x"])
def test_cast_timing(tmp_path, speed):
    cast = tmp_path / "timing.cast"
    events = [
        {"version": 2, "width": 80, "height": 24},
        [0, "o", "\x1b[41m\x1b[2J"],
        [0.6, "o", "\x1b[44m\x1b[2J"],
        [3, "o", "\x1b[42m\x1b[2J"],
    ]
    cast.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    output = tmp_path / "timing.mp4"
    args = ["--cast-file", str(cast), str(output)]
    if speed:
        args += ["--speed", speed]
    result = run(*args)
    assert result.returncode == 0, result.stderr
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(output)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert float(json.loads(probe.stdout)["format"]["duration"]) == pytest.approx(3.5, abs=0.2)
    for timestamp, channel in [(0.2, 0), (1.0, 2), (3.2, 1)]:
        frame = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(timestamp),
                "-i",
                str(output),
                "-frames:v",
                "1",
                "-vf",
                "scale=1:1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "pipe:1",
            ],
            capture_output=True,
            check=True,
        ).stdout
        assert len(frame) == 3
        assert frame[channel] - max(value for index, value in enumerate(frame) if index != channel) > 30
    assert not list(tmp_path.glob(".sh2mp4-*"))


def test_failed_command_still_creates_video(tmp_path):
    output = tmp_path / "failed.mp4"
    result = run("echo failed; exit 7", str(output), "--watch")
    assert result.returncode == 7, result.stderr
    assert output.stat().st_size > 0
    assert not list(tmp_path.glob(".sh2mp4-*"))


def test_bad_output_is_not_success(tmp_path):
    result = run("true", str(tmp_path / "missing" / "output.mp4"))
    assert result.returncode == 1
    assert "Recording complete:" not in result.stdout


def test_sigterm_cleans_up_capture(tmp_path):
    output = tmp_path / "interrupted.mp4"
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "sh2mp4", "sleep 60", str(output)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for line in process.stdout:
            if "waiting for command" in line:
                break
        else:
            pytest.fail(process.stderr.read())
        process.terminate()
        _, stderr = process.communicate(timeout=15)
        assert process.returncode == 143, stderr
        assert not list(tmp_path.glob(".sh2mp4-*"))
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()


@pytest.mark.parametrize("font,size", [("DejaVu Sans Mono", 12), ("Liberation Mono", 20)])
def test_actual_terminal_grid(tmp_path, font, size):
    import shlex

    grid = tmp_path / "grid.txt"
    result = run(
        f"stty size > {shlex.quote(str(grid))}",
        str(tmp_path / "grid.mp4"),
        "--font",
        font,
        "--font-size",
        str(size),
        "--cols",
        "81",
        "--lines",
        "25",
    )
    assert result.returncode == 0, result.stderr
    assert grid.read_text().strip() == "25 81"
