"""세 도구의 hook 설정이 같은 차단 스크립트를 가리키는지 검사한다."""
import json
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
    assert "scripts/block_dangerous.py" in entry["hooks"][0]["command"]


def test_references_are_write_protected():
    assert "Edit(/references/**)" in load(".claude/settings.json")["permissions"]["deny"]
