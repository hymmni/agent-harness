"""임시 저장소에서 실제 git 명령으로 .githooks 규칙을 검사한다."""
import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parent.parent / ".githooks"
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
GOOD = "feat(core): add thing\n\n- explain thing"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)


def commit(repo, message=GOOD, *flags):
    name = f"f{len(list(repo.iterdir()))}.txt"
    (repo / name).write_text("x\n")
    git(repo, "add", name)
    return git(repo, "commit", "-q", "-m", message, *flags)


@pytest.fixture
def empty_repo(tmp_path):
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "t")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "core.hooksPath", str(HOOKS))
    return path


@pytest.fixture
def repo(empty_repo):
    assert commit(empty_repo).returncode == 0
    return empty_repo


@pytest.fixture
def remote(repo, tmp_path):
    path = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(path)], check=True, env=ENV)
    git(repo, "remote", "add", "origin", str(path))
    return path


def test_first_commit_on_main_is_allowed(empty_repo):
    assert commit(empty_repo).returncode == 0


def test_second_commit_on_main_is_blocked(repo):
    result = commit(repo)
    assert result.returncode != 0 and "main" in result.stderr


@pytest.mark.parametrize("branch", ["feat/ok", "hotfix/can-timeout", "fix/a.b_c"])
def test_allowed_branch_names(repo, branch):
    git(repo, "switch", "-q", "-c", branch)
    assert commit(repo).returncode == 0


@pytest.mark.parametrize("branch", ["feature/x", "feat/Upper", "exp/x", "wip", "feat/한글"])
def test_blocked_branch_names(repo, branch):
    git(repo, "switch", "-q", "-c", branch)
    result = commit(repo)
    assert result.returncode != 0 and branch in result.stderr


def test_detached_head_commit_is_allowed(repo):
    git(repo, "switch", "-q", "--detach")
    assert commit(repo).returncode == 0


def test_local_merge_into_main_is_blocked(repo):
    git(repo, "switch", "-q", "-c", "feat/x")
    commit(repo)
    git(repo, "switch", "-q", "main")
    result = git(repo, "merge", "--no-ff", "--no-edit", "feat/x")
    assert result.returncode != 0 and "main" in result.stderr


def test_merge_between_feature_branches_is_allowed(repo):
    git(repo, "switch", "-q", "-c", "feat/y")
    commit(repo)
    git(repo, "switch", "-q", "-c", "feat/x", "HEAD~1")
    assert git(repo, "merge", "--no-ff", "--no-edit", "feat/y").returncode == 0


@pytest.mark.parametrize("message", ["add thing", "feat(core): add thing", "feat: add thing\n\n- x"])
def test_bad_commit_message_is_blocked(repo, message):
    git(repo, "switch", "-q", "-c", "feat/x")
    assert commit(repo, message).returncode != 0


@pytest.mark.parametrize("message", ["Merge branch 'x'", 'Revert "x"', "fixup! x", "squash! x"])
def test_generated_commit_message_is_allowed(repo, message):
    git(repo, "switch", "-q", "-c", "feat/x")
    assert commit(repo, message).returncode == 0


def test_first_push_of_main_is_allowed(repo, remote):
    assert git(repo, "push", "-q", "origin", "main").returncode == 0


def test_push_to_existing_main_is_blocked(repo, remote):
    git(repo, "push", "-q", "origin", "main")
    assert commit(repo, GOOD, "--no-verify").returncode == 0
    result = git(repo, "push", "-q", "origin", "main")
    assert result.returncode != 0 and "main" in result.stderr


def test_feature_branch_and_tag_push_are_allowed(repo, remote):
    git(repo, "push", "-q", "origin", "main")
    git(repo, "switch", "-q", "-c", "feat/x")
    commit(repo)
    git(repo, "tag", "v0.1.0", "main")
    assert git(repo, "push", "-q", "origin", "feat/x").returncode == 0
    assert git(repo, "push", "-q", "origin", "v0.1.0").returncode == 0


@pytest.mark.parametrize("name", ["pre-commit", "pre-merge-commit", "commit-msg", "pre-push"])
def test_hook_is_executable(name):
    assert os.access(HOOKS / name, os.X_OK)
