import io
import json

from sh2mp4.cast_output import render


def test_timing_uses_actual_first_event_not_process_exit(tmp_path, monkeypatch):
    ticks = iter([100.0, 100.375])
    monkeypatch.setattr("sh2mp4.cast_output.time.time", lambda: next(ticks))
    stream = iter(['{"version":2}', '[0,"o","start"]', '[0.375,"o","finish"]'])
    output = io.StringIO()
    path = tmp_path / "timing.json"
    render(stream, output, path)
    assert output.getvalue() == "startfinish"
    assert json.loads(path.read_text()) == {"start": 100, "end": 100.375}


def test_renderer_does_not_import_from_working_directory(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    import sh2mp4.cast_output

    (tmp_path / "json.py").write_text('raise RuntimeError("imported cwd")')
    path = tmp_path / "timing.json"
    script = Path(sh2mp4.cast_output.__file__)
    result = subprocess.run(
        [sys.executable, "-I", str(script), str(path)],
        cwd=tmp_path,
        input='{"version":2}\n[0,"o","hello"]\n',
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "hello"
    assert path.exists()
