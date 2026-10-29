import subprocess
from pathlib import Path


def test_coverage_preserves_test_failure(tmp_path):
    activate = tmp_path / ".venv/bin/activate"
    activate.parent.mkdir(parents=True)
    activate.write_text('pytest() { echo "failed tests"; return 7; }\n')
    script = Path(__file__).resolve().parents[1] / "scripts/coverage.sh"
    result = subprocess.run(["bash", str(script), "sh2mp4"], cwd=tmp_path, capture_output=True)
    assert result.returncode == 7
