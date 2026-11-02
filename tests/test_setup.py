"""가짜 에이전트 CLI를 둔 임시 저장소에서 setup.py를 실제로 실행해 검사한다."""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SETUP = Path(__file__).resolve().parent.parent / "scripts/setup.py"
GIT_DIR = str(Path(shutil.which("git")).parent)
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}

INSTALL = {
    "claude": "plugin install superpowers --marketplace anthropics/claude-plugins-official",
    "codex": "plugin add superpowers@openai-curated-remote",
    "agy": "plugin install https://github.com/obra/superpowers",
}
NOT_INSTALLED = "superpowers@x  not installed"
INSTALLED = "superpowers@x  installed, enabled"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)


def hooks_path(repo):
    return git(repo, "config", "core.hooksPath").stdout.strip()


@pytest.fixture
def bin_dir(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    return path


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    (path / "scripts").mkdir(parents=True)
    shutil.copy2(SETUP, path / "scripts/setup.py")
    git(path, "init", "-q", "-b", "main")
    return path


def fake_agent(bin_dir, name, listed=NOT_INSTALLED, install_exit=0):
    """호출 인자를 로그에 남긴다. `plugin list`는 listed를 출력한다."""
    path = bin_dir / name
    path.write_text(
        "#!/bin/sh\n"
        f'echo "$*" >> "{bin_dir}/{name}.log"\n'
        f'if [ "$1 $2" = "plugin list" ]; then echo "{listed}"; exit 0; fi\n'
        f"exit {install_exit}\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def calls(bin_dir, name):
    log = bin_dir / f"{name}.log"
    return log.read_text().splitlines() if log.exists() else []


def run_setup(repo, bin_dir):
    env = {**ENV, "PATH": f"{bin_dir}{os.pathsep}{GIT_DIR}"}
    return subprocess.run([sys.executable, "scripts/setup.py"], cwd=repo,
                          capture_output=True, text=True, env=env)


def test_connects_hooks_without_agents(repo, bin_dir):
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"


def test_keeps_other_hooks_path(repo, bin_dir):
    git(repo, "config", "core.hooksPath", ".husky")
    result = run_setup(repo, bin_dir)
    assert hooks_path(repo) == ".husky"
    assert ".husky" in result.stdout and result.returncode == 1


def test_keeps_user_hook(repo, bin_dir):
    (repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\n")
    result = run_setup(repo, bin_dir)
    assert hooks_path(repo) == ""
    assert "pre-commit" in result.stdout and result.returncode == 1


def test_sample_hooks_do_not_count(repo, bin_dir):
    (repo / ".git/hooks/pre-commit.sample").write_text("#!/bin/sh\n")
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"


def test_outside_git_repo_explains_git_init(tmp_path, bin_dir):
    path = tmp_path / "plain"
    (path / "scripts").mkdir(parents=True)
    shutil.copy2(SETUP, path / "scripts/setup.py")
    result = run_setup(path, bin_dir)
    assert "git init" in result.stdout and result.returncode == 1


def test_installs_superpowers_for_each_agent(repo, bin_dir):
    for name in INSTALL:
        fake_agent(bin_dir, name)
    assert run_setup(repo, bin_dir).returncode == 0
    for name, command in INSTALL.items():
        assert calls(bin_dir, name) == ["plugin list", command]


def test_not_installed_row_still_installs(repo, bin_dir):
    fake_agent(bin_dir, "codex", listed=NOT_INSTALLED)
    run_setup(repo, bin_dir)
    assert INSTALL["codex"] in calls(bin_dir, "codex")


def test_installed_plugin_is_skipped(repo, bin_dir):
    fake_agent(bin_dir, "codex", listed=INSTALLED)
    assert run_setup(repo, bin_dir).returncode == 0
    assert calls(bin_dir, "codex") == ["plugin list"]


def test_rerun_on_configured_clone_changes_nothing(repo, bin_dir):
    git(repo, "config", "core.hooksPath", ".githooks")
    fake_agent(bin_dir, "claude", listed=INSTALLED)
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"
    assert calls(bin_dir, "claude") == ["plugin list"]


def test_failed_install_continues_and_reports(repo, bin_dir):
    fake_agent(bin_dir, "codex", install_exit=1)
    fake_agent(bin_dir, "agy")
    result = run_setup(repo, bin_dir)
    assert INSTALL["agy"] in calls(bin_dir, "agy")
    assert INSTALL["codex"] in result.stdout and result.returncode == 1


def test_prints_manual_trust_steps(repo, bin_dir):
    fake_agent(bin_dir, "claude", listed=INSTALLED)
    fake_agent(bin_dir, "codex", listed=INSTALLED)
    out = run_setup(repo, bin_dir).stdout
    assert "폴더 신뢰" in out and "/hooks" in out
