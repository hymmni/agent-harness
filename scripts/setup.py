#!/usr/bin/env python3
"""
clone마다 한 번 실행하는 설정 스크립트. 여러 번 실행해도 결과가 같다.

1. git hook을 .githooks에 연결한다. git은 이 설정을 clone으로 전달하지 않는다.
2. 설치된 에이전트에 필수 플러그인 superpowers를 사용자 범위로 설치한다.
3. 자동화할 수 없는 승인 단계를 안내한다.

끝나지 않은 항목이 있으면 exit 1로 끝난다.
"""

import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = ".githooks"
COMMAND_TIMEOUT = 300
SUPERPOWERS = {
    "claude": ["claude", "plugin", "install", "superpowers",
               "--marketplace", "anthropics/claude-plugins-official"],
    "codex": ["codex", "plugin", "add", "superpowers@openai-curated-remote"],
    "agy": ["agy", "plugin", "install", "https://github.com/obra/superpowers"],
}
MANUAL_STEPS = {
    "claude": "Claude Code: 첫 실행 때 이 폴더 신뢰를 승인하세요.",
    "codex": "Codex: /hooks에서 이 레포의 hook을 승인하세요. 승인 전에는 위험 명령이 차단되지 않습니다.",
}


def run(*command: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace",
                          timeout=COMMAND_TIMEOUT)


def connect_git_hooks(root: Path) -> tuple[bool, str]:
    git = ("git", "-C", str(root))
    current = run(*git, "config", "core.hooksPath").stdout.strip()
    if current == HOOKS_DIR:
        return True, f"git hook: 이미 {HOOKS_DIR}에 연결되어 있습니다."
    if current:
        return False, f"git hook: core.hooksPath가 {current}라서 바꾸지 않았습니다. 하네스 규칙이 검사되지 않습니다."

    hooks = root / run(*git, "rev-parse", "--git-path", "hooks").stdout.strip()
    user_hooks = sorted(p.name for p in hooks.glob("*") if p.is_file() and p.suffix != ".sample")
    if user_hooks:
        return False, f"git hook: 기존 hook({', '.join(user_hooks)})이 있어 연결하지 않았습니다. 옮긴 뒤 다시 실행하세요."

    run(*git, "config", "core.hooksPath", HOOKS_DIR)
    return True, f"git hook: {HOOKS_DIR}에 연결했습니다."


def has_superpowers(agent: str) -> bool:
    listed = run(agent, "plugin", "list").stdout.splitlines()
    return any("superpowers" in line and "not installed" not in line for line in listed)


def install_superpowers(agent: str) -> tuple[bool, str]:
    command = SUPERPOWERS[agent]
    manual = f"{agent}: 설치 실패. 직접 실행하세요: {shlex.join(command)}"
    try:
        if has_superpowers(agent):
            return True, f"{agent}: superpowers가 이미 설치되어 있습니다."
        result = run(*command)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"{manual}\n  {e}"
    if result.returncode != 0:
        return False, f"{manual}\n  {result.stderr.strip()[-300:]}"
    return True, f"{agent}: superpowers를 설치했습니다."


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if run("git", "-C", str(root), "rev-parse", "--git-dir").returncode != 0:
        print("git 저장소가 아닙니다. 먼저 `git init`을 실행하세요.")
        return 1

    complete, message = connect_git_hooks(root)
    print(message)

    agents = [agent for agent in SUPERPOWERS if shutil.which(agent)]
    for agent in agents:
        done, message = install_superpowers(agent)
        print(message)
        complete = complete and done

    manual = [MANUAL_STEPS[agent] for agent in agents if agent in MANUAL_STEPS]
    if manual:
        print("\n직접 승인할 단계:")
        for step in manual:
            print(f"  - {step}")
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
