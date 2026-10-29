from sh2mp4.check_deps import check_runtime_dependencies


def test_required_tools_are_reported_in_all_modes(monkeypatch):
    monkeypatch.setattr("sh2mp4.check_deps.check_command", lambda cmd: cmd not in {"xprop", "xdpyinfo", "asciinema"})
    assert set(check_runtime_dependencies()) == {"xprop", "xdpyinfo", "asciinema"}


def test_playback_capability_is_required(monkeypatch):
    monkeypatch.setattr("sh2mp4.check_deps.check_command", lambda cmd: True)
    monkeypatch.setattr("sh2mp4.check_deps.check_asciinema_support", lambda: False)
    assert check_runtime_dependencies() == ["asciinema with --out-fmt asciicast support"]
