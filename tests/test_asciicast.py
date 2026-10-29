import os
import subprocess

from sh2mp4.asciicast import get_cast_command


def test_cast_filename_is_literal(tmp_path):
    player = tmp_path / "asciinema"
    player.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    player.chmod(0o755)
    cast = tmp_path / 'a "quote" $(printf INJECTED >&2) $HOME `echo bad`.cast'
    result = subprocess.run(
        ["bash", "-c", get_cast_command(cast)],
        env={**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines()[-1] == str(cast)
    assert not result.stderr
