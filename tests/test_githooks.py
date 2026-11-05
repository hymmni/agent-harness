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


@pytest.mark.parametrize("branch", [
    "feat/ok", "fix/a.b_c", "hotfix/can-timeout", "refactor/x", "docs/x", "chore/x",
])
def test_allowed_branch_names(repo, branch):
    git(repo, "switch", "-q", "-c", branch)
    assert commit(repo).returncode == 0


@pytest.mark.parametrize("branch", ["feature/x", "feat/Upper", "exp/x", "wip", "feat/한글"])
def test_blocked_branch_names(repo, branch):
    git(repo, "switch", "-q", "-c", branch)
    result = commit(repo)
    assert result.returncode != 0 and branch in result.stderr


def test_conflict_markers_block_commit(repo):
    git(repo, "switch", "-q", "-c", "feat/x")
    (repo / "rules.md").write_text("<<<<<<< before updating\na\n=======\nb\n>>>>>>> after updating\n")
    git(repo, "add", "rules.md")
    result = git(repo, "commit", "-q", "-m", GOOD)
    assert result.returncode != 0 and "충돌" in result.stderr


def test_detached_head_commit_is_allowed(repo):
    git(repo, "switch", "-q", "--detach")
    assert commit(repo).returncode == 0


def test_local_merge_into_main_is_blocked(repo):
    git(repo, "switch", "-q", "-c", "feat/x")
    commit(repo)
    git(repo, "switch", "-q", "main")
    result = git(repo, "merge", "--no-ff", "--no-edit", "feat/x")
    assert result.returncode != 0 and "main" in result.stderr


@pytest.fixture
def direct_repo(repo):
    """main_via_pr=false로 설치해 사람이 로컬에서 main에 병합하는 프로젝트."""
    (repo / ".copier-answers.yml").write_text("research: false\nmain_via_pr: false\n")
    return repo


def test_direct_mode_allows_commit_on_main(direct_repo):
    assert commit(direct_repo).returncode == 0


def test_direct_mode_allows_local_merge_into_main(direct_repo):
    git(direct_repo, "switch", "-q", "-c", "feat/x")
    commit(direct_repo)
    git(direct_repo, "switch", "-q", "main")
    assert git(direct_repo, "merge", "--no-ff", "--no-edit", "feat/x").returncode == 0


def test_direct_mode_allows_push_to_main(direct_repo, remote):
    git(direct_repo, "push", "-q", "origin", "main")
    assert commit(direct_repo).returncode == 0
    assert git(direct_repo, "push", "-q", "origin", "main").returncode == 0


def test_direct_mode_still_blocks_conflict_markers(direct_repo):
    (direct_repo / "c.txt").write_text("<<<<<<< before updating\nx\n")
    git(direct_repo, "add", "c.txt")
    assert git(direct_repo, "commit", "-q", "-m", GOOD).returncode != 0


def test_pr_mode_answer_blocks_commit_on_main(repo):
    (repo / ".copier-answers.yml").write_text("research: false\nmain_via_pr: true\n")
    assert commit(repo).returncode != 0


def test_merge_between_feature_branches_is_allowed(repo):
    git(repo, "switch", "-q", "-c", "feat/y")
    commit(repo)
    git(repo, "switch", "-q", "-c", "feat/x", "HEAD~1")
    assert git(repo, "merge", "--no-ff", "--no-edit", "feat/y").returncode == 0


@pytest.mark.parametrize("message", [
    "add thing", "feat(core): add thing", "feat: add thing\n\n- x", "Merge stuff", "Reverted x",
])
def test_bad_commit_message_is_blocked(repo, message):
    git(repo, "switch", "-q", "-c", "feat/x")
    assert commit(repo, message).returncode != 0


@pytest.mark.parametrize("message", [
    "Merge branch 'x'", "Merge branches 'a' and 'b'", "Merge remote-tracking branch 'origin/x'",
    "Merge tag 'v1'", "Merge commit 'abc'", "Merge pull request #1 from x/y",
    'Revert "x"', 'Reapply "x"', "fixup! x", "squash! x", "amend! x",
])
def test_generated_commit_message_is_allowed(repo, message):
    git(repo, "switch", "-q", "-c", "feat/x")
    assert commit(repo, message).returncode == 0


@pytest.mark.parametrize("kind", ["feat", "fix", "hotfix", "refactor", "docs", "chore", "test", "wip"])
def test_commit_types_are_allowed(repo, kind):
    git(repo, "switch", "-q", "-c", "feat/x")
    assert commit(repo, f"{kind}(core): add thing\n\n- explain thing").returncode == 0


@pytest.mark.parametrize("message", [
    # `git commit -v`의 diff는 scissors 줄 아래에 있고, 그 안의 삭제 줄이 `- `로 시작할 수 있다.
    "feat(core): add thing\n\n# ------------------------ >8 ------------------------\n- old line\n",
    "feat(core): add thing\n\n-no space\n",
])
def test_body_needs_a_real_bullet(tmp_path, message):
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text(message)
    assert subprocess.run([HOOKS / "commit-msg", path], capture_output=True).returncode != 0


def test_comment_above_message_is_ignored(tmp_path):
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("# template note\nfeat(core): add thing\n\n- explain thing\n")
    assert subprocess.run([HOOKS / "commit-msg", path], capture_output=True).returncode == 0


def test_first_push_of_main_is_allowed(repo, remote):
    assert git(repo, "push", "-q", "origin", "main").returncode == 0


def test_push_to_existing_main_is_blocked(repo, remote):
    git(repo, "push", "-q", "origin", "main")
    assert commit(repo, GOOD, "--no-verify").returncode == 0
    result = git(repo, "push", "-q", "origin", "main")
    assert result.returncode != 0 and "main" in result.stderr


def test_push_of_branch_onto_main_is_blocked(repo, remote):
    git(repo, "push", "-q", "origin", "main")
    git(repo, "switch", "-q", "-c", "feat/x")
    commit(repo)
    result = git(repo, "push", "-q", "origin", "feat/x:main")
    assert result.returncode != 0 and "main" in result.stderr


def add_remote_with_main(repo, tmp_path, name):
    path = tmp_path / f"{name}.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(path)], check=True, env=ENV)
    git(repo, "remote", "add", name, str(path))
    git(repo, "push", "-q", name, "main")
    assert commit(repo, GOOD, "--no-verify").returncode == 0


def test_main_can_sync_to_personal_fork(repo, tmp_path):
    add_remote_with_main(repo, tmp_path, "personal")
    assert git(repo, "push", "-q", "personal", "main").returncode == 0


def test_main_push_to_any_other_remote_is_blocked(repo, tmp_path):
    add_remote_with_main(repo, tmp_path, "upstream")
    result = git(repo, "push", "-q", "upstream", "main")
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


@pytest.mark.parametrize("name", ["pre-commit", "pre-merge-commit", "commit-msg", "pre-push"])
def test_hook_mode_reaches_new_clones(name):
    entry = subprocess.run(["git", "ls-files", "-s", f".githooks/{name}"], cwd=HOOKS.parent,
                           capture_output=True, text=True).stdout
    assert entry.startswith("100755")
