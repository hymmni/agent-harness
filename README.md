# Harness Framework: Robot Behavior Intelligence

이 저장소는 로봇 행동 지능(Diffusion Policy, Flow Matching 등) 연구를 위한 **드롭인(drop-in) 코드 하네스 템플릿**입니다. 작업할 베이스라인 레포지토리에 적용하면 Claude Code, Codex, Antigravity 중 어떤 에이전트를 쓰든 같은 규칙과 스킬, 안전장치로 구조화된 워크플로우(탐색 → 논의 → 플랜 작성 → 실행)를 따를 수 있습니다.

## 사전 준비

- Python 3
- 사용할 에이전트

## 적용 방법

**적용할 프로젝트 레포 루트에서** 실행합니다. 빈 프로젝트는 먼저 `mkdir <이름> && cd <이름> && git init`을 실행합니다.

```bash
git clone https://github.com/hymmni/claude-harness-framework.git harness && python3 harness/install.py
python3 .harness/setup.py
```

`install.py`는 파일 복사(비파괴) → `.gitignore` 병합 → 디렉토리 생성 → 클론 자가삭제까지 처리합니다. 기존 파일은 덮어쓰지 않으며, 기존 `AGENTS.md`나 `CLAUDE.md`가 있으면 harness 버전을 `*.harness.md`로 남겨 수동 병합하게 합니다. (대상 경로 확인을 건너뛰려면 끝에 ` --yes`)

### 팀원이 clone한 뒤

clone마다 한 번 실행합니다. 여러 번 실행해도 결과가 같습니다.

```bash
python3 .harness/setup.py
```

- git hook을 `.githooks/`에 연결합니다. 다른 hook이 이미 있으면 바꾸지 않고 알려 줍니다.
- 설치된 에이전트에 `superpowers` 플러그인을 사용자 범위로 설치합니다. 하네스의 필수 플러그인은 이것뿐이고, 나머지는 개인 선택입니다.

다음 승인은 자동화할 수 없어 직접 합니다.

- Claude Code: 첫 실행 때 폴더 신뢰를 승인합니다.
- Codex: `/hooks`에서 이 레포의 hook을 승인합니다. 승인 전에는 위험 명령이 차단되지 않습니다.

에이전트별로 알아 둘 점입니다.

- Codex는 로그인한 뒤에 `setup.py`를 실행합니다. 플러그인 목록을 받으려면 로그인이 필요합니다.
- `codex exec`의 `workspace-write` 샌드박스는 `.git`에 쓰지 못해 브랜치를 만들 수 없습니다.
- `agy -p`는 비대화형이라 셸 명령을 승인할 수 없습니다. 브랜치와 커밋 작업은 대화형 세션에서 합니다.

### 적용 후 구성

```
AGENTS.md        # 규칙의 단일 원본 — git 추적
CLAUDE.md        # AGENTS.md를 불러오는 한 줄 — git 추적
.agents/         # 공용 스킬, Antigravity hook — git 추적
.claude/         # Claude Code 설정과 스킬 안내 파일 (settings.json, skills/만 git 추적)
.codex/          # Codex hook — git 추적
.githooks/       # 브랜치·커밋 규칙 — git 추적
docs/            # 아키텍처 가이드 (ARCHITECTURE, ADR, ROBOT_GUIDE) — git 추적
  private/       #   PC/GPU 등 로컬 인프라 정보 (ENVIRONMENT.md) — git 미추적
.harness/        # 설정과 안전장치 스크립트 — git 추적
experiments/     # 브랜치별 실험 기록 (LOG_TEMPLATE 활용) — git 추적
references/      # 외부 오픈소스를 분석용으로 Clone (Read-only) — git 미추적
scratch/         # 일회용 스크립트 — git 미추적
.gitignore       # harness 산출물과 대용량 파일 제외 규칙
```

대상 프로젝트가 public 레포일 수 있어 인프라 정보(`docs/private/`)는 추적하지 않습니다. 워크플로우 실행 시 `docs/superpowers/plans/`에 플랜(`.md`)이 쌓입니다.

## 브랜치와 릴리즈

`main`과 `feat|fix|hotfix|refactor|docs|chore/<주제>` 브랜치만 쓰고, main 반영은 PR과 일반 병합으로 합니다. 릴리즈는 main의 `vX.Y.Z` 태그와 GitHub Release로 나눕니다. 자세한 규칙은 `AGENTS.md`를 참고하십시오. 강제는 지침과 hook까지이며 GitHub 서버 설정은 쓰지 않습니다.

`references/` 쓰기 차단은 Claude Code에서만 강제되고, 다른 에이전트는 `AGENTS.md`의 규칙에 의존합니다.

## 시작하기

상세한 사용법과 에이전트 협업 워크플로우는 `docs/ROBOT_GUIDE.md`를 참고하십시오.

## 템플릿 개발

이 템플릿 자체의 테스트는 다음 명령으로 실행합니다. `tests/`는 대상 프로젝트에 복사되지 않습니다.

```bash
python3 -m pytest -q tests
```
