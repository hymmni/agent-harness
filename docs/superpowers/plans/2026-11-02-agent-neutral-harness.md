# 에이전트 중립 하네스 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 하네스를 Claude Code, Codex, Antigravity 어느 쪽으로도 같은 규칙·스킬·안전장치로 쓸 수 있게 하고, 브랜치·릴리즈·산출물 규칙을 에이전트 수준에서 강제한다.

**Architecture:** `AGENTS.md`와 `.agents/skills/`를 단일 원본으로 두고 도구별 차이는 얇은 설정 파일에만 둔다. 안전장치는 공용 스크립트 하나와 git hook으로 구현하고, clone마다 실행하는 `scripts/setup.py`가 hook 연결과 `superpowers` 설치를 맡는다. 플랜은 별도 실행기 없이 에이전트 세션에서 실행한다.

**Tech Stack:** Python 3 표준 라이브러리, POSIX sh, git hook, pytest

**Spec:** `docs/superpowers/specs/2026-11-02-agent-neutral-harness-design.md`

## Global Constraints

- 작업 브랜치는 `feat/agent-neutral-harness`다. main에 직접 커밋하지 않는다.
- 커밋은 영어 Scoped Conventional Commits, 동사 중심 제목, `- ` 본문을 쓰고 세션의 attribution 줄로 끝낸다.
- 브랜치 이름: `^(feat|fix|hotfix|refactor|docs|chore)/[a-z0-9._-]+$`
- 커밋 제목: `^(feat|fix|hotfix|refactor|docs|chore|test|wip)\([^)]+\): .+`
- 대상 프로젝트로 복사되는 공용 문서(`AGENTS.md`, `.agents/skills/harness/SKILL.md`, `docs/ROBOT_GUIDE.md`, `docker-optional/`)에 특정 에이전트를 전제한 내용을 넣지 않는다.
- 새 의존성을 추가하지 않는다.
- 실제 에이전트 검증은 권한 우회 옵션 없이 한다. 정책에 막히면 우회하지 말고 사용자에게 알린다.
- 템플릿 전용 테스트는 `tests/`에 두고 대상 프로젝트에 복사하지 않는다.
- 필수 외부 의존성은 `superpowers`뿐이다. `mattpocock-skills`, `ponytail`, `i-have-adhd`는 공용 파일과 `setup.py`에 넣지 않는다.

## Review Focus

1. 대상 프로젝트의 기존 `.gitignore`가 `experiments/`를 제외하는 경우: 설치가 경고한다. Task 7이 테스트한다.
2. 대상 프로젝트에 `AGENTS.md` 없이 `CLAUDE.md`만 있는 경우: 기존 파일을 보존하고 `@AGENTS.md` 추가를 안내한다. Task 7이 테스트한다.
3. 대상 프로젝트에 다른 `core.hooksPath`나 `.git/hooks` 사용자 hook이 있는 경우: 덮어쓰지 않고 경고한다. Task 6이 테스트한다.
4. 설정이 끝난 clone에서 `setup.py`를 다시 실행하는 경우: 값을 바꾸지 않고 설치 명령도 실행하지 않는다. Task 6이 테스트한다.
5. 플러그인 설치가 실패하는 경우(오프라인, 오래된 CLI): 나머지를 계속 진행하고 실패한 명령을 출력한 뒤 exit 1로 끝난다. Task 6이 테스트한다.

---

### Task 1: 이전 작업을 브랜치로 옮겨 보존

**Files:**
- 기존 미커밋 변경 전부, `AGENTS.md`, `.agents/`, `.codex/`, `docs/superpowers/`

**Interfaces:**
- Produces: `feat/agent-neutral-harness` 브랜치

- [x] **Step 1: 브랜치 생성**

Run: `git switch -c feat/agent-neutral-harness`
Expected: 미커밋 변경을 유지한 채 전환됨

- [x] **Step 2: 기준 테스트 확인**

Run: `python3 -m pytest -q scripts`
Expected: `79 passed`

- [x] **Step 3: 안전장치 수정 커밋**

`docs/superpowers/`를 제외한 변경을 스테이징해 `fix(harness): make dangerous command hook actually block` 제목으로 커밋한다. 본문에 hook, deny 규칙, 중복 주입 제거, README 정리를 적는다.

- [x] **Step 4: 설계와 플랜 커밋**

`docs/superpowers/`를 스테이징해 `docs(harness): add agent-neutral harness design and plan` 제목으로 커밋한다.

---

### Task 2: 스케줄러, 실행기, 병합 스크립트, 빈 상태 시작 경로 삭제

**Files:**
- Delete: `scripts/scheduler.py`, `scripts/merge_to_main.py`, `scripts/execute.py`, `scripts/test_execute.py`
- Modify: `install.py`, `README.md`, `scripts/test_block_dangerous.py`

**Interfaces:**
- Produces: `--print-gitignore`가 없는 `install.py`. `gitignore_text()`는 `install_gitignore()`가 계속 쓰므로 유지한다.

- [x] **Step 1: 네 파일 삭제**

Run: `git rm scripts/scheduler.py scripts/merge_to_main.py scripts/execute.py scripts/test_execute.py`

- [x] **Step 2: `install.py` 정리**

`--print-gitignore` 인자와 그 분기, docstring 마지막의 from scratch 문단을 지운다.

- [x] **Step 3: README 정리**

"빈 상태에서 새로 시작" 절, "세션 리밋 이어가기" 절, `execute.py` 사용 설명을 지운다. 적용 방법 안내는 Task 9에서 다시 쓴다. `scripts/test_block_dangerous.py`의 허용 목록에 있는 `python3 scripts/execute.py plan.md`는 `python3 scripts/setup.py`로 바꾼다.

- [x] **Step 4: 검증**

Run: `python3 -m pytest -q scripts && python3 install.py --help | grep -c print-gitignore`
Expected: 테스트 통과, grep 결과 `0`

- [x] **Step 5: 커밋**

제목: `refactor(harness): remove scheduler, plan runner, merge helper, and scratch install path`

---

### Task 3: 규칙과 스킬을 단일 원본으로 통합

**Files:**
- Modify: `AGENTS.md`, `CLAUDE.md`, `.agents/skills/harness/SKILL.md`, `.claude/skills/harness/SKILL.md`
- Test: `tests/test_neutral_docs.py`

**Interfaces:**
- Produces: `FORBIDDEN` 패턴 목록과 `SHARED_FILES` 목록 (Task 8과 Task 9가 파일을 추가한다)

- [x] **Step 1: 실패하는 테스트 작성**

`SHARED_FILES = ["AGENTS.md", ".agents/skills/harness/SKILL.md"]`, `FORBIDDEN = r"claude|codex|antigravity|클로드|fable|opus|sonnet|haiku|AskUserQuestion|/compact|/clear|scheduler\.py|merge_to_main|execute\.py|state\.json|mattpocock|ponytail|i-have-adhd"` (대소문자 무시)로 다음을 검사한다.

```python
def test_claude_md_only_imports_agents_md():
    assert (ROOT / "CLAUDE.md").read_text().strip() == "@AGENTS.md"

@pytest.mark.parametrize("rel", SHARED_FILES)
def test_shared_file_names_no_agent(rel):
    assert not re.search(FORBIDDEN, (ROOT / rel).read_text(), re.IGNORECASE)

@pytest.mark.parametrize("text", [
    "feat|fix|hotfix|refactor|docs|chore", "scratch/", "experiments/<",
    "git checkout vX.Y.Z", "docker compose exec dev", "core.hooksPath",
    "pyproject.toml", "scripts/setup.py", "git revert",
])
def test_agents_md_states_rule(text):
    assert text in (ROOT / "AGENTS.md").read_text()

def test_claude_skill_points_to_shared_skill():
    pointer = (ROOT / ".claude/skills/harness/SKILL.md").read_text()
    shared = (ROOT / ".agents/skills/harness/SKILL.md").read_text()
    assert ".agents/skills/harness/SKILL.md" in pointer
    assert pointer.split("---")[1] == shared.split("---")[1]
    assert len(pointer.splitlines()) <= 8
```

- [x] **Step 2: 실패 확인**

Run: `python3 -m pytest -q tests/test_neutral_docs.py`
Expected: FAIL

- [x] **Step 3: `AGENTS.md` 재작성**

스펙 "규칙" 절의 변경을 적용하고 "브랜치와 릴리즈", "작업 산출물" 절을 규칙으로 옮긴다. `AGENTS.md 자체는...` 문장은 "이 문서는..."으로 바꾼다. `execute.py` 안내, 유틸리티 명령어의 삭제된 스크립트, 세션 연속 규칙을 지우고 큰 작업 전 토큰 규모 안내만 남긴다. 체크리스트의 `*.state.json` 항목과 `core.hooksPath` 항목은 스펙 문구대로 쓴다.

- [x] **Step 4: `CLAUDE.md`를 `@AGENTS.md` 한 줄로 교체**

- [x] **Step 5: 스킬 정리**

`.agents/skills/harness/SKILL.md`에서 도구 전용 표현, D절의 실행 티어, 커밋 압축 설명, 병합 절, frontmatter `description`의 `execute.py` 문구를 지운다. D절은 "플랜은 현재 세션에서 `superpowers:executing-plans`나 `superpowers:subagent-driven-development`로 실행하고 끝난 step은 플랜에서 체크한다"로 쓰고, 병합은 PR 설명으로 바꾼다. `.claude/skills/harness/SKILL.md`는 같은 frontmatter와 원본을 읽으라는 한 줄로 교체한다.

- [x] **Step 6: 통과 확인**

Run: `python3 -m pytest -q tests/test_neutral_docs.py scripts`
Expected: PASS

- [x] **Step 7: 커밋**

제목: `refactor(harness): make AGENTS.md the single agent-neutral source`

---

### Task 4: 차단 스크립트를 세 도구 공용으로 확장

**Files:**
- Modify: `scripts/block_dangerous.py`, `scripts/test_block_dangerous.py`
- Create: `.agents/hooks.json`
- Test: `tests/test_hook_configs.py`

**Interfaces:**
- Consumes: 기존 `DANGEROUS` 정규식, `main() -> int`
- Produces: 입력 형식별 차단. Claude·Codex는 stderr와 exit 2, Antigravity는 stdout JSON과 exit 0

- [x] **Step 1: 실패하는 테스트 추가**

```python
def run_antigravity(command):
    return run_hook(json.dumps({"toolCall": {"name": "run_command", "args": {"CommandLine": command}}}))

def test_antigravity_denied_with_json():
    result = run_antigravity("rm -rf build")
    assert result.returncode == 0
    decision = json.loads(result.stdout)
    assert decision["decision"] == "deny" and decision["reason"]

def test_antigravity_allowed_prints_nothing():
    result = run_antigravity("git status")
    assert result.returncode == 0 and result.stdout == ""
```

차단 목록에 `git commit --no-verify -m x`, `git push --no-verify`, `git commit -n -m x`, `git -c core.hooksPath=/dev/null commit -m x`, `git config core.hooksPath .git/hooks`, `git config --unset core.hooksPath`를 추가한다. 허용 목록에 `git config core.hooksPath`, `git config core.hooksPath .githooks`, `git commit -am "update"`를 추가한다.

`tests/test_hook_configs.py`는 세 설정을 읽어 검사한다: `.claude/settings.json`과 `.codex/hooks.json`은 `hooks.PreToolUse[0]`의 matcher가 `Bash`, `.agents/hooks.json`은 `harness-guard.PreToolUse[0]`의 matcher가 `run_command`이고, 모두 command에 `scripts/block_dangerous.py`가 들어 있다. `.claude/settings.json`의 `permissions.deny`에 `Edit(/references/**)`가 있는지도 검사한다.

- [x] **Step 2: 실패 확인**

Run: `python3 -m pytest -q scripts/test_block_dangerous.py tests/test_hook_configs.py`
Expected: 새 케이스 FAIL

- [x] **Step 3: 구현**

`tool_input.command`가 있으면 Claude·Codex 형식, `toolCall.args.CommandLine`이 있으면 Antigravity 형식으로 처리한다. 둘 다 없으면 stderr와 exit 2로 차단한다. `# ponytail:` 주석은 `# 문자열 매칭이라 \`rm -r -f\`나 스크립트 경유는 못 잡는다.`로 바꾼다. 정규식에 다음을 추가한다.

```python
r"|--no-verify"
r"|git\s+commit\b[^;&|]*\s-[a-z]*n\b"
r"|--unset[^;&|]*core\.hooksPath"
r"|core\.hooksPath(?!\s*(\.githooks)?\s*($|[;&|]))"
```

- [x] **Step 4: `.agents/hooks.json` 생성**

```json
{
  "harness-guard": {
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/scripts/block_dangerous.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [x] **Step 5: 통과 확인**

Run: `python3 -m pytest -q scripts tests`
Expected: PASS

- [x] **Step 6: 커밋**

제목: `feat(harness): share the dangerous command guard across agents`

---

### Task 5: git hook으로 브랜치와 커밋 규칙 강제

**Files:**
- Create: `.githooks/pre-commit`, `.githooks/pre-merge-commit`, `.githooks/commit-msg`, `.githooks/pre-push`
- Test: `tests/test_githooks.py`

**Interfaces:**
- Consumes: Global Constraints의 두 정규식
- Produces: 추적되는 `.githooks/` (모두 mode `100755`)

- [x] **Step 1: 실패하는 테스트 작성**

fixture는 임시 저장소를 `git init -b main`으로 만들고 `core.hooksPath`를 이 레포의 `.githooks` 절대경로로 설정한다. 커밋 메시지 `GOOD = "feat(core): add thing\n\n- explain thing"`을 쓴다. 실제 git 명령으로 다음을 검사한다.

| 테스트 | 기대 |
|---|---|
| 첫 커밋을 main에 | 성공 |
| 두 번째 커밋을 main에 | 실패, stderr에 `main` |
| `feat/ok`, `hotfix/can-timeout`, `fix/a.b_c` | 성공 |
| `feature/x`, `feat/Upper`, `exp/x`, `wip` | 실패 |
| detached HEAD 커밋 | 성공 |
| `feat/x`를 main에 `git merge --no-ff` | 실패 |
| `feat/x`에서 다른 브랜치 병합 | 성공 |
| 제목 `add thing` | 실패 |
| 본문 없는 `feat(core): add thing` | 실패 |
| `Merge branch 'x'`, `Revert "x"`, `fixup! x`, `squash! x` | 성공 |
| 빈 bare 원격에 main 첫 push | 성공 |
| 원격 main이 있을 때, 테스트에서 `--no-verify`로 만든 새 main 커밋을 push | 실패 |
| `feat/x` push, 태그 `v0.1.0` push | 성공 |
| `.githooks/*` 실행 권한 | 모두 있음 |

- [x] **Step 2: 실패 확인**

Run: `python3 -m pytest -q tests/test_githooks.py`
Expected: FAIL

- [x] **Step 3: hook 구현**

모두 POSIX sh로 쓰고 실패 시 이유와 올바른 방법을 stderr에 출력한다.
- `pre-commit`: `git rev-parse -q --verify HEAD`가 실패하면(첫 커밋) 통과한다. `git symbolic-ref -q --short HEAD`가 실패하면(detached) 통과한다. main이면 실패, 브랜치 정규식에 맞지 않으면 실패한다.
- `pre-merge-commit`: `exec "$(dirname "$0")/pre-commit"`
- `commit-msg`: `#` 주석을 빼고 검사한다. `Merge `, `Revert "`, `fixup! `, `squash! `로 시작하면 통과한다. 나머지는 제목 정규식과 본문의 `- ` 줄을 요구한다.
- `pre-push`: stdin의 `<local_ref> <local_sha> <remote_ref> <remote_sha>`를 읽는다. `remote_ref`가 `refs/heads/main`이고 `remote_sha`가 0으로만 이루어지지 않으면 실패한다.

- [x] **Step 4: 통과 확인**

Run: `python3 -m pytest -q scripts tests`
Expected: PASS

- [x] **Step 5: 이 레포에 적용하고 커밋**

Run: `git config core.hooksPath .githooks && git add --chmod=+x .githooks/* && git ls-files -s .githooks`
Expected: 네 파일 모두 `100755`

제목: `feat(harness): enforce branch and commit rules with git hooks`

---

### Task 6: clone별 설정 스크립트 추가

**Files:**
- Create: `scripts/setup.py`
- Test: `tests/test_setup.py`

**Interfaces:**
- Consumes: Task 5의 `.githooks/`
- Produces:
  - `SUPERPOWERS: dict[str, list[str]]`: 실행 파일 이름별 설치 명령
  - `connect_git_hooks(root: Path) -> tuple[bool, str]`: 완료 여부와 메시지
  - `install_superpowers(agent: str) -> tuple[bool, str]`: 완료 여부와 메시지
  - `main() -> int`: 전부 끝나면 0, 끝나지 않은 항목이 있으면 1

- [x] **Step 1: 실패하는 테스트 작성**

각 테스트는 임시 git 저장소에 `scripts/setup.py`를 복사하고 `sys.executable`로 실행한다. `PATH`에는 git이 있는 디렉터리와, 인자를 로그에 남기는 가짜 `claude`, `codex`, `agy`를 둔 디렉터리만 넣는다. 가짜 CLI의 `plugin list`는 테스트가 정한 문자열을 출력한다.

| 준비 상태 | 기대 |
|---|---|
| 에이전트 없음 | exit 0, `core.hooksPath`가 `.githooks` |
| `core.hooksPath=.husky` | 값 유지, 출력에 경고, exit 1 |
| `.git/hooks/pre-commit` 있음 | `core.hooksPath` 미설정, 출력에 경고, exit 1 |
| `.git/hooks/pre-commit.sample`만 있음 | `core.hooksPath`가 `.githooks`, exit 0 |
| git 저장소 아님 | 출력에 `git init`, exit 1 |
| 세 에이전트 모두 `superpowers` 없음 | `SUPERPOWERS`의 세 명령이 인자까지 그대로 호출됨, exit 0 |
| `plugin list`에 `superpowers@x  not installed` | 설치 명령 호출 |
| `plugin list`에 `superpowers@x  installed, enabled` | 설치 명령 호출 안 함 |
| 설정이 끝난 clone에서 다시 실행 | 값 유지, 설치 명령 호출 안 함, exit 0 |
| `codex` 설치만 실패 | `agy` 설치도 호출됨, 출력에 실패한 명령, exit 1 |
| `claude`, `codex` 있음 | 출력에 폴더 신뢰와 `/hooks` 안내 |

- [x] **Step 2: 실패 확인**

Run: `python3 -m pytest -q tests/test_setup.py`
Expected: FAIL

- [x] **Step 3: 구현**

`SUPERPOWERS`의 값은 다음과 같다.

```python
SUPERPOWERS = {
    "claude": ["claude", "plugin", "install", "superpowers",
               "--marketplace", "anthropics/claude-plugins-official"],
    "codex": ["codex", "plugin", "add", "superpowers@openai-curated-remote"],
    "agy": ["agy", "plugin", "install", "https://github.com/obra/superpowers"],
}
```

`connect_git_hooks`는 `core.hooksPath`가 비어 있고 `git rev-parse --git-path hooks` 안에 `.sample`이 아닌 파일이 없을 때만 설정한다. `install_superpowers`는 `shutil.which`로 찾지 못한 에이전트를 건너뛴다. `<agent> plugin list` 출력에 `superpowers`가 있고 `not installed`가 없는 줄이 있으면 설치된 것으로 본다. 설치 명령은 5분 제한으로 실행하고, 시간 초과도 실패로 처리한다. 마지막에 찾은 에이전트의 수동 승인 단계를 출력한다.

- [x] **Step 4: 통과 확인**

Run: `python3 -m pytest -q scripts tests`
Expected: PASS

- [x] **Step 5: 커밋**

제목: `feat(harness): add per-clone setup script`

---

### Task 7: 설치기, `.gitignore`, 실험 기록 양식 갱신

**Files:**
- Modify: `install.py`, `.gitignore`, `experiments/LOG_TEMPLATE.md`
- Test: `tests/test_install.py`

**Interfaces:**
- Consumes: Task 5의 `.githooks/`, Task 6의 `scripts/setup.py`
- Produces:
  - `CONFLICT_FILES = ("AGENTS.md", "CLAUDE.md")`
  - `HARNESS_DIRS = ("experiments", "references", "scratch")`
  - `warn_ignored_experiments(target: Path) -> Optional[str]`

- [x] **Step 1: 실패하는 테스트 작성**

각 테스트는 `project/harness`에 이 레포를 복사하고(`.git`, 캐시 제외) `python3 harness/install.py --yes --without-docker`를 실행한다.

| 준비 상태 | 기대 |
|---|---|
| 빈 git 저장소 | `AGENTS.md`, `CLAUDE.md`, `.githooks/`, `scratch/`, `scripts/setup.py` 생성, `core.hooksPath` 미설정, 출력에 `python3 scripts/setup.py`, `harness/`, `tests/`, `README.md` 없음, hook 실행 권한 유지 |
| 같은 설치 후 `git check-ignore` | 제외: `docs/private/x`, `references/x`, `scratch/x`, `a.pth`, `a.pt`, `a.ckpt`, `a.safetensors`, `d.zarr/x`, `a.hdf5`, `a.h5`, `wandb/x`, `outputs/x` |
| 같은 설치 후 `git check-ignore` | 추적: `experiments/feat-x/log.md`, `.claude/settings.json`, `.claude/skills/harness/SKILL.md`, `.agents/hooks.json`, `.codex/hooks.json` |
| `CLAUDE.md`만 있음 | 기존 내용 유지, `CLAUDE.harness.md` 생성, 출력에 `@AGENTS.md` |
| `AGENTS.md`가 있음 | 기존 내용 유지, `AGENTS.harness.md` 생성 |
| `.gitignore`에 `experiments/` 있음 | 출력에 경고 |
| git 저장소 아님 | 설치 성공 |

- [x] **Step 2: 실패 확인**

Run: `python3 -m pytest -q tests/test_install.py`
Expected: FAIL

- [x] **Step 3: `install.py` 구현**

존재 확인 기준을 `AGENTS.md`로 바꾸고 `TOP_EXCLUDE`에 `tests`를 추가한다. `CONFLICT_FILES`를 돌며 `*.harness.md`를 남기고, `CLAUDE.md` 충돌 시 `@AGENTS.md` 추가를 안내한다. `GITIGNORE_BLOCK`을 다음으로 바꾼다.

```text
/CLAUDE.harness.md
/AGENTS.harness.md
/.claude/*
!/.claude/skills/
!/.claude/settings.json
/docs/private/
/references/
/scratch/
/continuation_plan.md
*.pth
*.pt
*.ckpt
*.safetensors
*.zarr/
*.hdf5
*.h5
wandb/
outputs/
```

`warn_ignored_experiments`는 `git check-ignore -q experiments/feat-x/log.md`로 판단한다. 완료 메시지에서 도구 전용 명령을 빼고 `python3 scripts/setup.py` 실행을 안내한다.

- [x] **Step 4: `.gitignore`와 양식 갱신**

템플릿 `.gitignore`에 `scratch/`를 추가한다. `LOG_TEMPLATE.md` 첫 부분에 브랜치, commit, 설정·seed, 데이터 버전을 넣고, 결과 절에 지표, 판정(채택/미채택), 실패한 접근과 이유를 넣는다. 저장 경로 규칙 `experiments/<브랜치명의 / 를 - 로>/YYYY-MM-DD-주제.md`를 맨 위에 적는다.

- [x] **Step 5: 통과 확인**

Run: `python3 -m pytest -q scripts tests`
Expected: PASS

- [x] **Step 6: 커밋**

제목: `feat(install): adopt agent-neutral layout and track shared harness files`

---

### Task 8: Docker에서 에이전트 관련 내용 제거

**Files:**
- Modify: `docker-optional/docker-compose.yml`, `docker-optional/.devcontainer/devcontainer.json`, `docker-optional/DOCKER.md`, `docker-optional/docker/Dockerfile`, `tests/test_neutral_docs.py`

**Interfaces:**
- Consumes: Task 3의 `SHARED_FILES`, `FORBIDDEN`

- [x] **Step 1: 실패하는 테스트 작성**

`SHARED_FILES`에 `docker-optional/DOCKER.md`, `docker-optional/docker-compose.yml`, `docker-optional/.devcontainer/devcontainer.json`, `docker-optional/docker/Dockerfile`을 추가한다. 다음을 추가한다.

```python
def test_devcontainer_installs_no_agent():
    config = json.loads((ROOT / "docker-optional/.devcontainer/devcontainer.json").read_text())
    assert "postCreateCommand" not in config and "onCreateCommand" not in config
    assert not any("node" in feature for feature in config["features"])

def test_compose_mounts_no_home():
    compose = (ROOT / "docker-optional/docker-compose.yml").read_text()
    assert "HOME=" not in compose and "${HOME}" not in compose

def test_dockerfile_has_no_foreign_reference():
    assert "self-improving-gym" not in (ROOT / "docker-optional/docker/Dockerfile").read_text()
```

- [x] **Step 2: 실패 확인**

Run: `python3 -m pytest -q tests/test_neutral_docs.py`
Expected: FAIL

- [x] **Step 3: 구현**

compose에서 설정 마운트 주석과 두 줄, `HOME`을 지운다. devcontainer에서 Node feature, `onCreateCommand`, `postCreateCommand`를 지우고 `common-utils`, `remoteUser`, `updateRemoteUserUID`는 유지한다. Dockerfile의 참조 주석을 일반 문구로 바꾼다. `DOCKER.md`의 CLI 설명과 "왜 non-root" 절을 지우고 "에이전트는 컨테이너 밖에서 실행하고 코드 실행은 `docker compose exec dev <명령>`으로 한다"와 "non-root는 마운트된 파일이 root 소유가 되는 것을 막는다"로 대체한다.

- [x] **Step 4: 통과 확인**

Run: `python3 -m pytest -q scripts tests`
Expected: PASS

- [x] **Step 5: 커밋**

제목: `refactor(docker): keep the scaffold as a plain dev environment`

---

### Task 9: 사용 문서 정리

**Files:**
- Modify: `README.md`, `docs/README.md`, `docs/ROBOT_GUIDE.md`, `.gitignore`, `tests/test_neutral_docs.py`

**Interfaces:**
- Consumes: 앞선 task의 모든 이름과 명령

- [x] **Step 1: 공용 문서 테스트 확장**

`tests/test_neutral_docs.py`의 `SHARED_FILES`에 `docs/ROBOT_GUIDE.md`를 추가한다.

Run: `python3 -m pytest -q tests/test_neutral_docs.py`
Expected: FAIL

- [x] **Step 2: README 재작성**

사전 준비는 "Python 3, 사용할 에이전트"로 쓴다. 적용 방법은 레포 루트에서 실행하는 한 줄로 합치고, 빈 프로젝트는 `mkdir <이름> && cd <이름> && git init` 후 같은 명령을 쓰게 한다. 설치 직후와 팀원의 clone 직후에는 `python3 scripts/setup.py`를 실행한다고 적는다. 필수 플러그인은 `superpowers`뿐이고 나머지는 개인 선택이라고 적는다. 구성 표는 스펙 기준으로 갱신한다. Claude Code 폴더 신뢰와 Codex `/hooks` 승인도 적는다.

- [x] **Step 3: 나머지 문서 정리**

`ROBOT_GUIDE.md`에서 도구 이름을 빼고 파일 목록과 추적 범위를 스펙에 맞춘다. 템플릿 `.gitignore` 주석의 `CLAUDE.md`를 `AGENTS.md`로 바꾼다.

- [x] **Step 4: 잔여 참조 검사**

Run: `python3 -m pytest -q scripts tests && grep -rInE "scheduler|merge_to_main|execute\.py|HARNESS_AGENT|state\.json|ponytail|print-gitignore|CLAUDE_TOOL_INPUT|exp/\*" README.md docs/*.md install.py scripts AGENTS.md .agents .claude/skills`
Expected: 테스트 통과, grep 출력 없음

- [x] **Step 5: 커밋**

제목: `docs(harness): document agent-neutral setup and workflow`

---

### Task 10: 실제 에이전트로 검증

**Files:**
- Create: `experiments/feat-agent-neutral-harness/2026-11-02-agent-neutral-verification.md`
- 나머지는 scratchpad의 일회용 저장소에서만 작업

**Interfaces:**
- Consumes: 모든 task의 결과물

- [x] **Step 1: 지시 파일 로드 확인**

일회용 저장소에 설치하고 `AGENTS.md`에 코드워드를 넣는다. `claude -p`, `codex exec --sandbox read-only -`, `agy -p`에 stdin으로 코드워드와 `harness` 스킬의 설명을 묻는다.
Expected: 세 도구 모두 코드워드와 스킬 설명을 답한다.

- [x] **Step 2: hook 차단 확인**

`rm -rf victim`을 시키고 `victim/`이 남는지 본다. 각 도구마다 `.claude/settings.json`, `.codex/hooks.json`, `.agents/hooks.json`이 없는 대조군을 함께 돌린다. Codex는 `/hooks` 신뢰 승인이 필요하니 사용자에게 요청한다.
Expected: 대조군은 삭제되거나 권한으로 막히고, hook이 있는 쪽은 차단 사유가 hook에서 나온다. 대조군도 막혀서 구분되지 않으면 미검증으로 기록한다. Antigravity hook에 별도 승인이 필요하면 README와 `setup.py` 안내에 추가한다.

- [x] **Step 3: `setup.py` 확인**

일회용 저장소를 새로 clone하고 `HOME`을 scratchpad의 빈 디렉터리로 바꿔 `python3 scripts/setup.py`를 실행한다. 사용자의 실제 에이전트 설정은 건드리지 않는다.
Expected: `core.hooksPath`가 `.githooks`이고 세 도구의 `plugin list`에 `superpowers`가 나온다. 실패하면 원인을 기록하고 `SUPERPOWERS` 표를 고친다. Codex처럼 로그인 없이 확인할 수 없는 항목은 미검증으로 기록한다.

- [x] **Step 4: 브랜치와 커밋 규칙 확인**

일회용 저장소에서 세 도구에게 파일 하나를 추가해 새 `feat/*` 브랜치에 커밋하게 한다. 허용 범위는 git과 파일 쓰기로 좁히고 권한 우회 옵션은 쓰지 않는다.
Expected: 규칙에 맞는 브랜치에 `commit-msg`를 통과한 커밋이 생긴다. 실패한 도구는 원인을 기록한다.

- [x] **Step 5: 전체 테스트**

Run: `python3 -m pytest -q scripts tests`
Expected: PASS

- [x] **Step 6: 결과 기록**

스펙의 "구현 시 확인할 것" 항목별로 통과, 실패, 미검증을 기록한다. 템플릿 레포에서는 `experiments/`가 제외되므로 이 파일은 커밋되지 않는다.

- [x] **Step 7: 보고**

push와 PR은 사용자 확인 후에 진행한다. 이 레포는 `.githooks`가 켜져 있으므로 PR로 main에 합친다.
