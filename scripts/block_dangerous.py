#!/usr/bin/env python3
"""
PreToolUse 훅 — 위험한 Bash 명령을 차단한다. Claude Code와 Codex가 공용으로 쓴다.

입력은 stdin JSON의 tool_input.command 이고, 차단은 exit 2 다 (exit 1은 차단되지 않는다).
입력을 읽지 못하면 통과시키지 않고 차단한다 — 훅이 조용히 무력화되는 것을 막기 위해서다.
"""

import json
import re
import sys

# ponytail: 문자열 매칭이라 `rm -r -f`나 스크립트 경유는 못 잡는다. 무인 실행의 격리는 컨테이너 몫이다.
DANGEROUS = re.compile(
    r"\brm\s+-[a-z]*(r[a-z]*f|f[a-z]*r)"
    r"|git\s+push\b[^;&|]*\s(--force|-f)\b"
    r"|git\s+reset\s+--hard"
    r"|DROP\s+TABLE",
    re.IGNORECASE,
)


def main() -> int:
    try:
        command = json.load(sys.stdin)["tool_input"]["command"]
    except (ValueError, KeyError, TypeError) as e:
        print(f"BLOCKED: 훅 입력을 읽지 못했습니다 ({e!r}).", file=sys.stderr)
        return 2
    if DANGEROUS.search(command):
        print("BLOCKED: 위험한 명령어가 감지되었습니다.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
