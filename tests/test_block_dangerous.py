"""block_dangerous.py 검증 — 실제 훅과 같은 방식(stdin JSON + 종료 코드)으로 실행한다."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".harness/block_dangerous.py"


def run_hook(stdin: str) -> subprocess.CompletedProcess:
    # git 저장소 밖에서 실행한다. 이 레포가 main에 있을 때 main 검사가 결과를 바꾸지 않게 한다.
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True,
                          cwd=os.path.abspath(os.sep))


def run_command(command: str) -> subprocess.CompletedProcess:
    return run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))


def assert_blocked(result: subprocess.CompletedProcess) -> None:
    # 파일이 없을 때 python3도 2로 끝나므로, 종료 코드만 보면 잘못된 이유로 통과한다.
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


@pytest.mark.parametrize("command", [
    "rm -rf build",
    "rm -fr build",
    "rm -Rf build",
    "cd /tmp && rm -rf x",
    "git push --force",
    "git push origin main --force",
    "git push -f origin main",
    "git reset --hard HEAD~1",
    "psql -c 'DROP TABLE runs'",
    "psql -c 'drop table runs'",
    "git commit --no-verify -m x",
    "git push --no-verify",
    "git commit -n -m x",
    "git -c core.hooksPath=/dev/null commit -m x",
    "git config core.hooksPath .git/hooks",
    "git config --unset core.hooksPath",
    "gh pr merge 3 --merge",
    "cd /tmp && gh pr merge",
    "rm -v -rf x",
    "rm -r -f x",
    "rm -f -r x",
    "rm --recursive --force x",
    "git -C . reset --hard",
    "git -C . push --force",
    "git reset HEAD~1 --hard",
    "git push -uf origin x",
    "git push origin +feat/x",
    "git clean -fdx",
    "git clean --force",
    "git commit -nm x",
    "git -C . commit -n -m x",
    "git push origin feat/x --force-with-lease",
])
def test_blocks_dangerous_command(command):
    assert_blocked(run_command(command))


def test_message_names_the_matched_text():
    assert "git reset --hard" in run_command("ls; git reset --hard HEAD~1").stderr


@pytest.mark.parametrize("command", [
    "rm build/out.log",
    "rm -f build/out.r",
    "rm -r build",
    "confirm -rf",
    "git push origin feat/fix-force",
    "git reset --soft HEAD~1",
    "python3 .harness/setup.py",
    "git config core.hooksPath",
    "git config core.hooksPath .githooks",
    "grep -n core.hooksPath AGENTS.md",
    'git commit -am "update"',
    "gh pr create --fill",
    "gh pr view 3",
    'test "$(git config core.hooksPath)" = .githooks && echo ok',
    "git config core.hooksPath 2>/dev/null",
    "git config --get core.hooksPath",
    "git commit -F msg.txt\ngit log -n 1",
    "python train.py --no-verify-ssl",
    "git clean -nd",
    "git push --follow-tags origin feat/x",
    "git commit --amend --no-edit",
])
def test_allows_ordinary_command(command):
    assert run_command(command).returncode == 0


UNREADABLE = [
    "", "not json", "{}", '{"tool_input": {}}', "null",
    '{"tool_input": {"command": 5}}',
    '{"toolCall": {}}',
    '{"toolCall": {"args": {"CommandLine": 5}}}',
    pytest.param("[" * 200_000, id="deep-json"),
]


@pytest.mark.parametrize("stdin", UNREADABLE)
def test_unreadable_input_is_blocked(stdin):
    assert_blocked(run_hook(stdin))


@pytest.mark.parametrize("stdin", UNREADABLE)
def test_unreadable_input_denies_on_stdout_too(stdin):
    # 어느 도구의 입력인지 모르므로, stdout으로 판단하는 도구에서도 차단되게 한다.
    assert json.loads(run_hook(stdin).stdout)["decision"] == "deny"


def run_antigravity(command: str) -> subprocess.CompletedProcess:
    return run_hook(json.dumps({"toolCall": {"name": "run_command", "args": {"CommandLine": command}}}))


def test_antigravity_denied_with_json():
    result = run_antigravity("rm -rf build")
    assert result.returncode == 0
    decision = json.loads(result.stdout)
    assert decision["decision"] == "deny" and decision["reason"]


def test_antigravity_allowed_prints_nothing():
    result = run_antigravity("git status")
    assert result.returncode == 0 and result.stdout == ""


# main 보호: 에이전트는 main에 커밋·병합·push하지 않는다. 사람은 터미널에서 직접 한다.
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}


def make_repo(path, branch=None, commit=True):
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True, env=GIT_ENV)
    if commit:
        subprocess.run(["git", "-C", str(path), "commit", "-q", "--allow-empty", "-m", "x"], check=True, env=GIT_ENV)
    if branch:
        subprocess.run(["git", "-C", str(path), "switch", "-q", "-c", branch], check=True, env=GIT_ENV)
    return path


def run_in(repo, command):
    return run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}))


@pytest.fixture
def main_repo(tmp_path):
    return make_repo(tmp_path / "repo")


@pytest.fixture
def feature_repo(tmp_path):
    return make_repo(tmp_path / "repo", branch="feat/x")


@pytest.mark.parametrize("command", [
    "git commit -m x", 'git commit -am "x"', "git merge feat/x", "git merge --no-ff --no-edit feat/x",
    "git cherry-pick abc123", "git revert HEAD", "git rebase feat/x", "git am fix.patch",
    "git push", "git push origin", "git push origin HEAD", "git push -u origin HEAD",
])
def test_blocks_changing_main_on_main(main_repo, command):
    assert_blocked(run_in(main_repo, command))


@pytest.mark.parametrize("command", [
    "git push origin main", "git push origin main && ls -f", "git push origin feat/x:main",
    "git push origin HEAD:refs/heads/main", "git push --all origin",
    "git switch main && git merge feat/x", "git checkout main; git commit -m x",
])
def test_blocks_changing_main_from_a_feature_branch(feature_repo, command):
    assert_blocked(run_in(feature_repo, command))


@pytest.mark.parametrize("command", [
    "git commit -m x", "git merge main", "git merge --no-edit origin/main", "git push", "git push -u origin HEAD",
    "git push origin feat/x", "git push origin feat/main-fix", "git switch main", "git commit-tree HEAD^{tree}",
])
def test_allows_feature_branch_work(feature_repo, command):
    assert run_in(feature_repo, command).returncode == 0


@pytest.mark.parametrize("command", [
    "git pull --ff-only origin main", "git fetch origin main", "git switch -c feat/y", "git log main",
    "git push origin v1.0.0", "git tag v1.0.0", "git status",
])
def test_allows_syncing_and_reading_main(main_repo, command):
    assert run_in(main_repo, command).returncode == 0


@pytest.mark.parametrize("command", [
    "git switch -c feat/y && git commit -m x",
    "git checkout -b feat/y; git commit -m x",
    "git switch -c feat/y && git push -u origin HEAD",
])
def test_allows_new_branch_created_in_the_same_command(main_repo, command):
    assert run_in(main_repo, command).returncode == 0


def test_checking_out_a_file_does_not_hide_main(main_repo):
    assert_blocked(run_in(main_repo, "git checkout README.md && git commit -am x"))


@pytest.fixture
def both(tmp_path):
    """작업 폴더는 main, 다른 레포는 기능 브랜치 — 그 반대도 쓴다."""
    return make_repo(tmp_path / "on-main"), make_repo(tmp_path / "on-feature", branch="feat/x")


def test_git_dash_c_uses_that_repo_branch(both):
    on_main, on_feature = both
    assert run_in(on_main, f"git -C {on_feature} commit -m x").returncode == 0
    assert_blocked(run_in(on_feature, f"git -C {on_main} commit -m x"))


def test_cd_uses_that_repo_branch(both):
    on_main, on_feature = both
    assert run_in(on_main, f"cd {on_feature} && git push").returncode == 0
    assert_blocked(run_in(on_feature, f"cd {on_main} && git commit -m x"))


def test_first_commit_on_empty_main_is_allowed(tmp_path):
    assert run_in(make_repo(tmp_path / "repo", commit=False), "git commit -m x").returncode == 0


def test_main_block_tells_human_to_run_it(main_repo):
    assert "터미널" in run_in(main_repo, "git merge feat/x").stderr


def test_antigravity_main_block_uses_its_cwd(main_repo):
    payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "git commit -m x", "Cwd": str(main_repo)}}}
    result = run_hook(json.dumps(payload))
    assert result.returncode == 0 and json.loads(result.stdout)["decision"] == "deny"
