#!/usr/bin/env python3
"""Regression: handoffs.json must reject shell-placeholder content."""
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "scripts" / "handoff.py"

def test_reject_shell_placeholder():
    bad = "$(cat /tmp/handoffs.json)\n"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write(bad)
        path = f.name
    result = subprocess.run(
        ["python3", str(HANDOFF), "--file", path, "validate"],
        capture_output=True, text=True
    )
    assert result.returncode != 0, "should reject shell placeholder"
    assert "shell-placeholder" in result.stdout.lower() or "handoff error" in result.stdout.lower()
    Path(path).unlink()

def test_valid_current_passes():
    result = subprocess.run(
        ["python3", str(HANDOFF), "validate"],
        capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["valid"] is True
    assert data["items"] >= 14

if __name__ == "__main__":
    test_reject_shell_placeholder()
    test_valid_current_passes()
    print("OK")
