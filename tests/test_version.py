import subprocess
import sys
from pathlib import Path
from importlib.metadata import version

import sh2mp4


def test_installed_version():
    assert sh2mp4.__version__ == version("sh2mp4")


def test_source_only_import():
    source = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            f"import sys; sys.path.insert(0, {source!r}); import sh2mp4; print(sh2mp4.__version__)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "0+unknown"
