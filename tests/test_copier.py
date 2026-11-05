"""copier로 하네스를 설치하고 갱신한다. 템플릿은 이 레포에서 git이 clone할 파일만 담은 임시 저장소다."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENV = {
    **os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "XDG_CONFIG_HOME": os.devnull,
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
}
HARNESS_TOP = {
    ".agents", ".claude", ".codex", ".githooks", ".harness", "AGENTS.md", "CLAUDE.md", "docs",
    ".copier-answers.yml", ".github",
}
DOCKER_TOP = {
    "DOCKER.md", "docker-compose.yml", "docker-compose.gpu.yml", ".env.example", "requirements.txt",
    "docker", ".devcontainer",
}
HOOK_NAMES = ("pre-commit", "pre-merge-commit", "commit-msg", "pre-push")
RESEARCH_FILES = ("docs/RESEARCH.md", ".harness/LOG_TEMPLATE.md", "docs/private/ENVIRONMENT.md")
RELEASE_FILES = (".github/workflows/release.yml", ".github/release-please-config.json",
                 ".github/.release-please-manifest.json")


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)


def make_template(path):
    """이 레포의 현재 작업 트리 중 git이 clone할 파일만 담아 커밋한다."""
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                            cwd=ROOT, check=True, capture_output=True, text=True).stdout
    for rel in listed.splitlines():
        src = ROOT / rel
        if src.is_file():
            dst = path / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    git(path, "init", "-q", "-b", "main")
    # 이 레포에서 추적하지만 .gitignore에 걸리는 파일(docs/private/ 아래)도 커밋해야 한다.
    git(path, "add", "-A", "-f")
    git(path, "commit", "-qm", "template")
    return path


def copier(command, *args, cwd):
    return subprocess.run([sys.executable, "-m", "copier", command, "--defaults", *args], cwd=cwd,
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, env=ENV)


def install(template, project, *data):
    options = [arg for item in data for arg in ("--data", item)]
    return copier("copy", *options, str(template), str(project), cwd=project)


def top_names(project):
    return {path.name for path in project.iterdir()} - {".git"}


@pytest.fixture(scope="session")
def template(tmp_path_factory):
    return make_template(tmp_path_factory.mktemp("template"))


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "project"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    return path


def test_installs_only_harness_files(template, project):
    result = install(template, project)
    assert result.returncode == 0, result.stderr
    assert top_names(project) == HARNESS_TOP


def test_excludes_only_root_readme(template, project):
    install(template, project)
    assert (project / "docs/README.md").is_file()


def test_research_files_need_research(template, project):
    install(template, project)
    assert [rel for rel in RESEARCH_FILES if (project / rel).exists()] == []
    assert not (project / "docs/private").exists()


def test_research_installs_research_files(template, project):
    assert install(template, project, "research=true").returncode == 0
    assert [rel for rel in RESEARCH_FILES if not (project / rel).is_file()] == []


def test_pr_mode_gets_only_the_release_pr_workflow(template, project):
    """템플릿 자신의 이슈 양식과 릴리즈 설정은 가져가지 않는다."""
    install(template, project)
    assert {str(path.relative_to(project)) for path in (project / ".github").rglob("*")} == {
        ".github/workflows", *RELEASE_FILES}
    workflow = (project / RELEASE_FILES[0]).read_text(encoding="utf-8")
    assert all(f": {rel}\n" in workflow for rel in RELEASE_FILES[1:])
    assert json.loads((project / RELEASE_FILES[2]).read_text(encoding="utf-8")) == {".": "0.0.0"}


def test_direct_mode_has_no_release_pr(template, project):
    assert install(template, project, "main_via_pr=false").returncode == 0
    assert ".github" not in top_names(project)


def test_answers_are_one_line_each_for_hooks(template, project):
    install(template, project)
    lines = (project / ".copier-answers.yml").read_text(encoding="utf-8").splitlines()
    assert "research: false" in lines and "main_via_pr: true" in lines


def test_update_can_turn_research_on(tmp_path, project):
    install(make_template(tmp_path / "template"), project)
    git(project, "add", "-A")
    git(project, "commit", "-qm", "adopt")
    result = copier("update", "--data", "research=true", cwd=project)
    assert result.returncode == 0, result.stderr
    assert (project / "docs/RESEARCH.md").is_file()


@pytest.mark.parametrize("name", HOOK_NAMES)
def test_hooks_stay_executable(template, project, name):
    install(template, project)
    assert os.access(project / ".githooks" / name, os.X_OK)


def test_docker_scaffold_is_opt_in(template, project):
    assert install(template, project, "with_docker=true").returncode == 0
    assert DOCKER_TOP <= top_names(project)
    compose = (project / "docker-compose.yml").read_text(encoding="utf-8")
    devcontainer = json.loads((project / ".devcontainer/devcontainer.json").read_text(encoding="utf-8"))
    assert "image: project/dev:latest" in compose
    assert devcontainer["name"] == "project dev"


def test_existing_fill_in_docs_are_kept(template, project):
    (project / "docs").mkdir()
    (project / "docs/ADR.md").write_text("mine\n")
    assert install(template, project).returncode == 0
    assert (project / "docs/ADR.md").read_text() == "mine\n"


def test_update_merges_template_change_with_local_edit(tmp_path, project):
    template = make_template(tmp_path / "template")
    install(template, project)
    git(project, "add", "-A")
    git(project, "commit", "-qm", "adopt")

    agents = project / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\n- local rule\n", encoding="utf-8")
    git(project, "commit", "-qam", "local")

    upstream = template / "AGENTS.md"
    title, rest = upstream.read_text(encoding="utf-8").split("\n", 1)
    upstream.write_text(f"{title} v2\n{rest}", encoding="utf-8")
    git(template, "commit", "-qam", "v2")

    result = copier("update", cwd=project)
    assert result.returncode == 0, result.stderr
    merged = agents.read_text(encoding="utf-8")
    assert merged.startswith(f"{title} v2\n") and merged.endswith("- local rule\n")


def test_readme_removal_lists_every_installed_path(template, project):
    """하네스 제거 절차가 설치되는 최상위 경로를 빠뜨리지 않는다."""
    install(template, project, "research=true", "with_docker=true", "main_via_pr=true")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("### 하네스 제거", 1)[1].split("\n## ", 1)[0]
    assert [name for name in sorted(top_names(project)) if f"`{name}" not in section] == []
