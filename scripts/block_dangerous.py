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

# 문자열 매칭이라 `rm -r -f`나 스크립트 경유는 못 잡는다.
DANGEROUS = re.compile(
    r"\brm\s+-[a-z]*(r[a-z]*f|f[a-z]*r)"
    r"|git\s+push\b[^;&|]*\s(--force|-f)\b"
    r"|git\s+reset\s+--hard"
    r"|DROP\s+TABLE"
    r"|--no-verify"
    r"|git\s+commit\b[^;&|]*\s-[a-z]*n\b"
    r"|--unset[^;&|]*core\.hooksPath"
    r"|core\.hooksPath(?!\s*(\.githooks)?\s*($|[;&|]))",
    re.IGNORECASE,
)
BLOCKED = "BLOCKED: 위험한 명령어가 감지되었습니다."


def deny_json(reason: str) -> str:
    return json.dumps({"decision": "deny", "reason": reason}, ensure_ascii=False)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        antigravity = "toolCall" in payload
        command = (payload["toolCall"]["args"]["CommandLine"] if antigravity
                   else payload["tool_input"]["command"])
        dangerous = DANGEROUS.search(command)
    except (ValueError, KeyError, TypeError) as e:
        reason = f"BLOCKED: 훅 입력을 읽지 못했습니다 ({e!r})."
        print(deny_json(reason))
        print(reason, file=sys.stderr)
        return 2
    if not dangerous:
        return 0
    if antigravity:
        print(deny_json(BLOCKED))
        return 0
    print(BLOCKED, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
