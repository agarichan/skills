from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_delegate_dry_run_outputs_valid_json_with_expected_fields() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    cmd = [
        "python3",
        "skills/codex-task-delegate/scripts/codex_wrapper.py",
        "delegate",
        "--dry-run",
        "hello",
    ]

    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(proc.stdout)
    assert payload["mode"] == "dry-run"

    command = payload["command"]
    assert isinstance(command, list)
    command_text = " ".join(command)
    assert "codex" in command_text
    assert "hello" in command_text
