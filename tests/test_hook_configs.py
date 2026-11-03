"""세 도구의 hook 설정이 같은 차단 스크립트를 가리키는지 검사한다."""
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


@pytest.mark.parametrize("entry, matcher", [
    (load(".claude/settings.json")["hooks"]["PreToolUse"][0], "Bash"),
    (load(".codex/hooks.json")["hooks"]["PreToolUse"][0], "Bash"),
    (load(".agents/hooks.json")["harness-guard"]["PreToolUse"][0], "run_command"),
])
def test_hook_runs_shared_guard(entry, matcher):
    assert entry["matcher"] == matcher
    assert ".harness/block_dangerous.py" in entry["hooks"][0]["command"]


@pytest.mark.parametrize("entry, payload", [
    (load(".claude/settings.json")["hooks"]["PreToolUse"][0], {"tool_input": {"command": "rm -rf x"}}),
    (load(".codex/hooks.json")["hooks"]["PreToolUse"][0], {"tool_input": {"command": "rm -rf x"}}),
    (load(".agents/hooks.json")["harness-guard"]["PreToolUse"][0],
     {"toolCall": {"args": {"CommandLine": "rm -rf x"}}}),
])
def test_hook_command_runs_from_the_project(entry, payload):
    result = subprocess.run(["sh", "-c", entry["hooks"][0]["command"]], cwd=ROOT, input=json.dumps(payload),
                            capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)})
    assert "rm -rf x" in result.stdout + result.stderr


def test_references_are_write_protected():
    assert "Edit(/references/**)" in load(".claude/settings.json")["permissions"]["deny"]
