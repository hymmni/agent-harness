"""block_dangerous.py 검증 — 실제 훅과 같은 방식(stdin JSON + 종료 코드)으로 실행한다."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent.parent / ".harness/block_dangerous.py"


def run_hook(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True)


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
    "git push origin main",
    "git push origin feat/fix-force",
    "git push origin main && ls -f",
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
