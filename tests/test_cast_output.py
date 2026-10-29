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
