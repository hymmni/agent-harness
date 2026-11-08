"""대상 프로젝트로 복사되는 공용 문서가 특정 에이전트를 전제하지 않는지 검사한다."""
import json
import re
from pathlib import Path

import pytest
import yaml   # copier가 함께 설치한다

ROOT = Path(__file__).resolve().parent.parent


def docker(name):
    """copier가 with_docker를 고른 경우에만 만드는 경로."""
    return f"{{% if with_docker %}}{name}{{% endif %}}"


COMPOSE = docker("docker-compose.yml") + ".jinja"
DEVCONTAINER = docker(".devcontainer") + "/devcontainer.json.jinja"
DOCKERFILE = docker("docker") + "/Dockerfile"
RESEARCH_DOC = "docs/{% if research %}RESEARCH.md{% endif %}"   # research를 고른 경우에만 설치
SHARED_FILES = [
    "AGENTS.md", ".agents/skills/harness/SKILL.md", RESEARCH_DOC, "docs/ARCHITECTURE.md", "docs/ADR.md",
    docker("DOCKER.md"), COMPOSE, DEVCONTAINER, DOCKERFILE,
]
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
    "feat|fix|refactor|docs|chore", "scratch/", "git merge --no-ff", "git tag -a", "release-please", "1.0.0 전에는", "자리표시",
    "git checkout vX.Y.Z", "docker compose exec dev", "core.hooksPath",
    "pyproject.toml", ".harness/setup.py", "git revert", "rebase", "copier update --defaults",
    "main_via_pr", "docs/RESEARCH.md", "`docs/private/`에 쓴다", "사용자가 제안할 때만 쓴다", "_src_path", "gh issue create -R", "--label bug",
    "하네스 파일을 직접 고치지 않는다", "터미널에서 직접 실행", "멈추고 사용자의 결정을 따른다",
])
def test_agents_md_states_rule(text):
    assert text in (ROOT / "AGENTS.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("rel", ["docs/ARCHITECTURE.md", "docs/ADR.md"])
def test_fill_in_docs_carry_the_placeholder_mark(rel):
    """AGENTS.md는 이 표시로 아직 채우지 않은 문서를 알아본다."""
    assert "자리표시" in (ROOT / rel).read_text(encoding="utf-8")


ISSUE_FORMS = sorted((ROOT / ".github/ISSUE_TEMPLATE").glob("*.yml"))


def test_template_repo_has_bug_and_improvement_forms():
    assert [path.stem for path in ISSUE_FORMS] == ["bug", "improvement"]


@pytest.mark.parametrize("path", ISSUE_FORMS, ids=lambda path: path.stem)
def test_issue_form_warns_that_the_repo_is_public(path):
    form = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert form["name"] and form["description"] and form["labels"] in (["bug"], ["enhancement"])
    assert form["body"][0]["type"] == "markdown" and "public" in form["body"][0]["attributes"]["value"]
    assert any(item.get("validations", {}).get("required") for item in form["body"])


@pytest.mark.parametrize("text", ["experiments/", "LOG_TEMPLATE", "ENVIRONMENT.md", "personal"])
def test_agents_md_leaves_research_rules_to_research_doc(text):
    assert text not in (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_agents_md_does_not_allow_patching_the_harness_in_a_project():
    """프로젝트에서 고친 하네스 파일은 copier update 뒤에도 남아 템플릿 수정과 겹친다."""
    assert "먼저 고치고" not in (ROOT / "AGENTS.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("text", [
    "experiments/<", ".harness/LOG_TEMPLATE.md", "git add -f", "personal",
    "`docs/private/ENVIRONMENT.md`가 없으면", "git checkout vX.Y.Z",
])
def test_research_doc_states_rule(text):
    assert text in (ROOT / RESEARCH_DOC).read_text(encoding="utf-8")


def test_agents_md_lists_commit_types_the_hook_allows():
    hook = (ROOT / ".githooks/commit-msg").read_text(encoding="utf-8")
    types = re.search(r"\^\(([a-z|]+)\)", hook).group(1)
    assert f"`{types}`" in (ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_claude_skill_points_to_shared_skill():
    pointer = (ROOT / ".claude/skills/harness/SKILL.md").read_text(encoding="utf-8")
    shared = (ROOT / ".agents/skills/harness/SKILL.md").read_text(encoding="utf-8")
    assert ".agents/skills/harness/SKILL.md" in pointer
    assert pointer.split("---")[1] == shared.split("---")[1]
    assert len(pointer.splitlines()) <= 8


def test_devcontainer_installs_no_agent():
    text = (ROOT / DEVCONTAINER).read_text(encoding="utf-8")
    config = json.loads(text)
    assert "postCreateCommand" not in config and "onCreateCommand" not in config
    assert not any("node" in feature for feature in config["features"])


def test_compose_mounts_no_home():
    compose = (ROOT / COMPOSE).read_text(encoding="utf-8")
    assert "HOME=" not in compose and "${HOME}" not in compose


def test_dockerfile_has_no_foreign_reference():
    dockerfile = (ROOT / DOCKERFILE).read_text(encoding="utf-8")
    assert "self-improving-gym" not in dockerfile
