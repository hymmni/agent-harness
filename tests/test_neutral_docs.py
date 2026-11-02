"""대상 프로젝트로 복사되는 공용 문서가 특정 에이전트를 전제하지 않는지 검사한다."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SHARED_FILES = ["AGENTS.md", ".agents/skills/harness/SKILL.md"]
FORBIDDEN = (
    r"claude|codex|antigravity|클로드|fable|opus|sonnet|haiku|AskUserQuestion|/compact|/clear"
    r"|scheduler\.py|merge_to_main|execute\.py|state\.json|mattpocock|ponytail|i-have-adhd"
)


def test_claude_md_only_imports_agents_md():
    assert (ROOT / "CLAUDE.md").read_text(encoding="utf-8").strip() == "@AGENTS.md"


@pytest.mark.parametrize("rel", SHARED_FILES)
def test_shared_file_names_no_agent(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert not re.search(FORBIDDEN, text, re.IGNORECASE)


@pytest.mark.parametrize("text", [
    "feat|fix|hotfix|refactor|docs|chore", "scratch/", "experiments/<",
    "git checkout vX.Y.Z", "docker compose exec dev", "core.hooksPath",
    "pyproject.toml", "scripts/setup.py", "git revert",
])
def test_agents_md_states_rule(text):
    assert text in (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_claude_skill_points_to_shared_skill():
    pointer = (ROOT / ".claude/skills/harness/SKILL.md").read_text(encoding="utf-8")
    shared = (ROOT / ".agents/skills/harness/SKILL.md").read_text(encoding="utf-8")
    assert ".agents/skills/harness/SKILL.md" in pointer
    assert pointer.split("---")[1] == shared.split("---")[1]
    assert len(pointer.splitlines()) <= 8
