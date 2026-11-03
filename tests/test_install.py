"""clone과 같은 구성의 harness/를 임시 프로젝트에 두고 install.py를 실제로 실행한다."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}

IGNORED = [
    "docs/private/x", "references/x", "scratch/x", "experiments/feat-x/log.md", "a.pth", "a.pt",
    "a.ckpt", "a.safetensors", "d.zarr/x", "symlinked.zarr", "a.hdf5", "a.h5", "wandb/x", "outputs/x",
    "CLAUDE.harness.md", "AGENTS.harness.md", "continuation_plan.md",
]
TRACKED = [
    ".claude/settings.json", ".claude/skills/harness/SKILL.md", ".agents/hooks.json",
    ".codex/hooks.json", ".harness/setup.py", ".harness/block_dangerous.py", ".harness/LOG_TEMPLATE.md",
]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)


def place_harness(project, name="harness"):
    """git이 clone할 파일만 harness/로 복사한다."""
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                            cwd=ROOT, check=True, capture_output=True, text=True).stdout
    for rel in listed.splitlines():
        src = ROOT / rel
        if src.is_file():
            dst = project / name / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def install(project):
    place_harness(project)
    return subprocess.run(
        [sys.executable, "harness/install.py", "--yes", "--without-docker"],
        cwd=project, capture_output=True, text=True, env=ENV,
    )


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "project"
    path.mkdir()
    git(path, "init", "-q")
    return path


def test_installs_into_empty_repo(project):
    result = install(project)
    assert result.returncode == 0
    for rel in ("AGENTS.md", "CLAUDE.md", ".githooks/pre-commit", "scratch",
                ".harness/setup.py", ".harness/block_dangerous.py"):
        assert (project / rel).exists(), rel
    for rel in ("harness", "tests", "scripts", "README.md", "docs/superpowers"):
        assert not (project / rel).exists(), rel
    assert os.access(project / ".githooks/pre-commit", os.X_OK)


def test_leaves_git_hooks_to_setup(project):
    result = install(project)
    assert git(project, "config", "core.hooksPath").stdout == ""
    assert "python3 .harness/setup.py" in result.stdout


@pytest.mark.parametrize("rel", IGNORED)
def test_ignores_local_and_large_files(project, rel):
    install(project)
    assert git(project, "check-ignore", "-q", rel).returncode == 0


@pytest.mark.parametrize("rel", TRACKED)
def test_tracks_shared_files(project, rel):
    install(project)
    assert git(project, "check-ignore", "-q", rel).returncode == 1


def test_keeps_existing_claude_md(project):
    (project / "CLAUDE.md").write_text("mine\n")
    result = install(project)
    assert (project / "CLAUDE.md").read_text() == "mine\n"
    assert (project / "CLAUDE.harness.md").exists()
    assert "@AGENTS.md" in result.stdout


def test_keeps_existing_agents_md(project):
    (project / "AGENTS.md").write_text("mine\n")
    install(project)
    assert (project / "AGENTS.md").read_text() == "mine\n"
    assert (project / "AGENTS.harness.md").exists()


def test_reports_skipped_existing_files(project):
    (project / ".claude").mkdir()
    (project / ".claude/settings.json").write_text("{}\n")
    result = install(project)
    assert (project / ".claude/settings.json").read_text() == "{}\n"
    assert ".claude/settings.json" in result.stdout


def test_refuses_clone_with_other_name(project):
    place_harness(project, "template")
    result = subprocess.run([sys.executable, "template/install.py", "--yes", "--without-docker"],
                            cwd=project, capture_output=True, text=True, env=ENV)
    assert result.returncode == 1
    assert (project / "template/install.py").exists()
    assert not (project / "AGENTS.md").exists()


def test_declined_confirmation_changes_nothing(project):
    place_harness(project)
    result = subprocess.run([sys.executable, "harness/install.py", "--without-docker"], cwd=project,
                            input="n\n", capture_output=True, text=True, env=ENV)
    assert result.returncode == 1
    assert (project / "harness/install.py").exists() and not (project / "AGENTS.md").exists()


def test_docker_scaffold_uses_project_name_and_ignores_env(project):
    place_harness(project)
    subprocess.run([sys.executable, "harness/install.py", "--yes", "--with-docker"], cwd=project,
                   capture_output=True, text=True, env=ENV)
    compose = (project / "docker-compose.yml").read_text(encoding="utf-8")
    assert "project/dev" in compose and "__PROJECT_NAME__" not in compose
    assert git(project, "check-ignore", "-q", ".env").returncode == 0


def test_second_gitignore_install_changes_nothing(project):
    install(project)
    before = (project / ".gitignore").read_text()
    install(project)
    assert (project / ".gitignore").read_text() == before


def test_replaces_outdated_managed_gitignore_block(project):
    begin = "# >>> harness gitignore (managed) >>>"
    end = "# <<< harness gitignore (managed) <<<"
    (project / ".gitignore").write_text(f"before\n\n{begin}\n/docs/\n{end}\n\nafter\n")
    install(project)
    text = (project / ".gitignore").read_text()
    assert "/docs/\n" not in text and "/scratch/" in text and text.count(begin) == 1
    assert text.startswith("before\n\n") and text.endswith("\n\nafter\n")


def test_installs_outside_git_repo(tmp_path):
    path = tmp_path / "plain"
    path.mkdir()
    assert install(path).returncode == 0
    assert (path / "AGENTS.md").exists()
