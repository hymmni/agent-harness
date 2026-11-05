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
    ".copier-answers.yml",
}
DOCKER_TOP = {
    "DOCKER.md", "docker-compose.yml", "docker-compose.gpu.yml", ".env.example", "requirements.txt",
    "docker", ".devcontainer",
}
HOOK_NAMES = ("pre-commit", "pre-merge-commit", "commit-msg", "pre-push")


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
    git(path, "add", "-A")
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
    text = upstream.read_text(encoding="utf-8")
    upstream.write_text(text.replace("# Harness Framework", "# Harness Framework v2", 1), encoding="utf-8")
    git(template, "commit", "-qam", "v2")

    result = copier("update", cwd=project)
    assert result.returncode == 0, result.stderr
    merged = agents.read_text(encoding="utf-8")
    assert merged.startswith("# Harness Framework v2") and merged.endswith("- local rule\n")
