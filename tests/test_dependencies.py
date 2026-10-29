from sh2mp4.check_deps import check_runtime_dependencies


def test_required_tools_are_reported_in_all_modes(monkeypatch):
    monkeypatch.setattr("sh2mp4.check_deps.check_command", lambda cmd: cmd not in {"xprop", "xdpyinfo", "asciinema"})
    for cast in (False, True):
        assert set(check_runtime_dependencies(cast)) == {"xprop", "xdpyinfo", "asciinema"}
