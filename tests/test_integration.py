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
    cast.write_text('{"version":2,"width":80,"height":24}\n[0,"o","start\\r\\n"]\n[3,"o","finish\\r\\n"]\n')
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
