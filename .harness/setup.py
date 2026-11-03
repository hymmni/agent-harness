#!/usr/bin/env python3
"""
clone마다 한 번 실행하는 설정 스크립트. 여러 번 실행해도 결과가 같다.

1. git hook을 .githooks에 연결한다. git은 이 설정을 clone으로 전달하지 않는다.
2. .gitignore의 하네스 블록을 최신 내용으로 맞춘다. copier는 기존 파일에 덧붙이지 못해 여기서 한다.
3. 하네스 공유 파일이 팀원에게 전달되는 상태인지 검사한다.
4. 설치된 에이전트에 필수 플러그인 superpowers를 사용자 범위로 설치한다.
5. 자동화할 수 없는 승인 단계를 안내한다.

끝나지 않은 항목이 있으면 exit 1로 끝난다.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = ".githooks"
SHARED_FILES = (
    "AGENTS.md", "CLAUDE.md",
    ".agents/hooks.json", ".agents/skills/harness/SKILL.md",
    ".claude/settings.json", ".claude/skills/harness/SKILL.md",
    ".codex/hooks.json",
    ".githooks/commit-msg", ".githooks/pre-commit", ".githooks/pre-merge-commit", ".githooks/pre-push",
    ".harness/LOG_TEMPLATE.md", ".harness/block_dangerous.py", ".harness/setup.py",
    "docs/ADR.md", "docs/ARCHITECTURE.md", "docs/ROBOT_GUIDE.md",
)
GITIGNORE_BEGIN = "# >>> harness gitignore (managed) >>>"
GITIGNORE_END = "# <<< harness gitignore (managed) <<<"
GITIGNORE_BLOCK = f"""{GITIGNORE_BEGIN}
/.claude/*
!/.claude/skills/
!/.claude/settings.json
/docs/private/
/experiments/
/references/
/scratch/
/continuation_plan.md
.env
*.pth
*.pt
*.ckpt
*.safetensors
*.zarr
*.hdf5
*.h5
wandb/
outputs/
{GITIGNORE_END}
"""
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
                          stdin=subprocess.DEVNULL, timeout=COMMAND_TIMEOUT)


def connect_git_hooks(root: Path) -> tuple[bool, str]:
    git = ("git", "-C", str(root))
    toplevel = run(*git, "rev-parse", "--show-toplevel").stdout.strip()
    if Path(toplevel).resolve() != root:
        return False, f"git hook: 하네스가 저장소 루트({toplevel})에 없어 연결하지 않았습니다. 루트에 설치하세요."

    current = run(*git, "config", "core.hooksPath").stdout.strip()
    if current == HOOKS_DIR:
        return True, f"git hook: 이미 {HOOKS_DIR}에 연결되어 있습니다."
    if current:
        return False, f"git hook: core.hooksPath가 {current}라서 바꾸지 않았습니다. 하네스 규칙이 검사되지 않습니다."

    hooks = root / run(*git, "rev-parse", "--git-path", "hooks").stdout.strip()
    user_hooks = sorted(p.name for p in hooks.glob("*") if p.is_file() and p.suffix != ".sample")
    if user_hooks:
        return False, f"git hook: 기존 hook({', '.join(user_hooks)})이 있어 연결하지 않았습니다. 옮긴 뒤 다시 실행하세요."

    result = run(*git, "config", "core.hooksPath", HOOKS_DIR)
    if result.returncode != 0:
        return False, f"git hook: 연결하지 못했습니다. {result.stderr.strip()}"
    return True, f"git hook: {HOOKS_DIR}에 연결했습니다."


def gitignore_with_block(text: str) -> str:
    """하네스 블록이 있으면 최신 내용으로 바꾸고, 없으면 끝에 붙인다. 블록 밖은 그대로 둔다."""
    block = re.compile(f"{re.escape(GITIGNORE_BEGIN)}.*?{re.escape(GITIGNORE_END)}\n?", re.DOTALL)
    if block.search(text):
        return block.sub(lambda _: GITIGNORE_BLOCK, text, count=1)
    if not text.strip():
        return GITIGNORE_BLOCK
    return text.rstrip("\n") + "\n\n" + GITIGNORE_BLOCK


def update_gitignore(root: Path) -> str | None:
    path = root / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = gitignore_with_block(text)
    if updated == text:
        return None
    path.write_text(updated, encoding="utf-8")
    return ".gitignore: 하네스 블록을 최신 내용으로 맞췄습니다. 이 변경도 커밋하세요."


def shared_file_problems(root: Path) -> list[str]:
    problems = []
    for rel in SHARED_FILES:
        path = root / rel
        if not path.is_file():
            problems.append(f"{rel}: 파일이 없습니다.")
        elif run("git", "-C", str(root), "check-ignore", "-q", rel).returncode == 0:
            problems.append(f"{rel}: .gitignore에 제외되어 팀원에게 전달되지 않습니다.")
        elif rel.startswith(HOOKS_DIR) and not os.access(path, os.X_OK):
            problems.append(f"{rel}: 실행 권한이 없어 git이 실행하지 않습니다.")
    claude_md = root / "CLAUDE.md"
    if claude_md.is_file() and "@AGENTS.md" not in claude_md.read_text(encoding="utf-8"):
        problems.append("CLAUDE.md: `@AGENTS.md` 줄이 없어 Claude Code가 규칙을 읽지 못합니다.")
    return problems


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

    message = update_gitignore(root)
    if message:
        print(message)

    problems = shared_file_problems(root)
    for problem in problems:
        print(f"공유 파일: {problem}")
    complete = complete and not problems

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
