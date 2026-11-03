#!/usr/bin/env python3
"""
PreToolUse 훅 — 위험한 셸 명령을 차단한다. 세 에이전트가 공용으로 쓴다.

| 도구              | 명령 필드                  | 차단 방식                      |
| Claude Code·Codex | tool_input.command         | stderr + exit 2                |
| Antigravity       | toolCall.args.CommandLine  | stdout의 deny JSON + exit 0    |

입력을 읽지 못하면 통과시키지 않고 차단한다 — 훅이 조용히 무력화되는 것을 막기 위해서다.
어느 도구의 입력인지 알 수 없으므로 이때는 두 방식을 모두 쓴다.
"""

import json
import re
import sys

# 사고를 막는 문자열 매칭이다. 스크립트 경유나 공백이 든 `git -C "a b"`는 못 잡고, 커밋 메시지 안의
# ` -n` 같은 글자는 잘못 잡는다. 잘못 잡히면 메시지를 파일로 넘기는 `git commit -F`를 쓴다.
GIT = r"\bgit(?:\s+-c\s+\S+|\s+--[\w-]+(?:=\S+)?)*\s+"   # git -C dir, -c k=v, --git-dir=x
SAME = r"[^;&|\n]*"                                      # 같은 셸 명령 안
DANGEROUS = re.compile(
    rf"\brm(?={SAME}\s(-[a-z]*r|--recursive))(?={SAME}\s(-[a-z]*f|--force)){SAME}"
    rf"|{GIT}push\b{SAME}\s(--force|-[a-z]*f[a-z]*\b|\+\S)"
    rf"|{GIT}reset\b{SAME}\s--hard"
    rf"|{GIT}clean\b{SAME}\s(-[a-z]*f|--force)"
    r"|DROP\s+TABLE"
    rf"|\bgit\b{SAME}\s--no-verify\b"
    rf"|{GIT}commit\b{SAME}\s-[a-z]*n[a-z]*\b"
    rf"|\bgit\b{SAME}\bunset\S*\s{SAME}core\.hooksPath"
    rf"|\bgit\b{SAME}core\.hooksPath="
    rf"|\bgit\b{SAME}core\.hooksPath[ \t]+(?!\.githooks[ \t]*($|[;&|)\n]))(?![012]?>|#|[;&|)])\S"
    r"|\bgh\s+pr\s+merge\b",
    re.IGNORECASE,
)


def deny_json(reason: str) -> str:
    return json.dumps({"decision": "deny", "reason": reason})


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        antigravity = "toolCall" in payload
        command = (payload["toolCall"]["args"]["CommandLine"] if antigravity
                   else payload["tool_input"]["command"])
        dangerous = DANGEROUS.search(command)
    except Exception as e:
        reason = f"BLOCKED: 훅 입력을 읽지 못했습니다 ({e!r})."
        print(deny_json(reason))
        print(reason, file=sys.stderr)
        return 2
    if not dangerous:
        return 0
    reason = f"BLOCKED: 위험한 명령어가 감지되었습니다: {dangerous.group(0)}"
    if antigravity:
        print(deny_json(reason))
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
