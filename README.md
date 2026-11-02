# Harness Framework: Robot Behavior Intelligence

이 저장소는 로봇 행동 지능(Diffusion Policy, Flow Matching 등) 연구를 위한 **드롭인(drop-in) 코드 하네스 템플릿**입니다. 작업할 베이스라인 레포지토리에 아래 하네스 파일들을 복사해 넣으면, 클로드와 함께 구조화된 워크플로우(탐색 → 논의 → 플랜 작성 → 실행)로 코드를 이식하고 실험할 수 있습니다.

## 사전 준비

- Python 3와 Claude Code
- `superpowers` 플러그인: harness 스킬의 브레인스토밍·플랜 작성 단계가 사용합니다. Claude Code에서 `/plugin install superpowers@claude-plugins-official`로 설치합니다.

## 적용 방법

상황에 맞는 **한 줄**을 복사해 실행하면 클론부터 세팅까지 끝납니다.

### ▶ 이미 코드가 있는 프로젝트에 적용 (adoption)

**적용할 프로젝트 레포 루트에서** 실행:

```bash
git clone https://github.com/hymmni/claude-harness-framework.git harness && python3 harness/install.py
```

`harness/`로 클론한 뒤 `install.py`가 파일 복사(비파괴) → `.gitignore` 병합 → 디렉토리 생성 →
클론 자가삭제까지 처리합니다. 기존 파일은 덮어쓰지 않으며, 기존 `CLAUDE.md`가 있으면 harness
버전을 `CLAUDE.harness.md`로 남겨 수동 병합하게 합니다. (대상 경로 확인을 건너뛰려면 끝에 ` --yes`)

### 적용 후 구성

```
CLAUDE.md        # 프로젝트 규칙 및 로봇 연구 프로토콜 (git 추적)
.claude/         # 클로드 설정 (git 미추적), harness 스킬 (skills/, git 추적)
docs/            # 아키텍처 가이드 (ARCHITECTURE, ADR, ROBOT_GUIDE) — git 추적
  private/       #   PC/GPU 등 로컬 인프라 정보 (ENVIRONMENT.md) — git 미추적
scripts/         # 안전장치 스크립트 — git 추적
experiments/     # 실험 결과 기록 (LOG_TEMPLATE 활용) — git 미추적
references/      # 외부 오픈소스를 분석용으로 Clone (Read-only) — git 미추적
.gitignore       # harness 산출물 제외 규칙
```

`CLAUDE.md`, `docs/`(단 `docs/private/` 제외), `scripts/`, `.claude/skills/`는 작업 코드와 함께 git 이력으로 관리되고, 나머지 하네스 파일(`.claude/` 나머지, `experiments/`, `references/`, `docs/private/`)은 로컬 전용입니다 — 대상 프로젝트가 public 레포일 수 있어, 인프라 정보 자체는 굳이 공개하지 않도록 설계했습니다. 워크플로우 실행 시 `docs/superpowers/plans/`에 플랜(`.md`)이 쌓입니다.

## 시작하기
상세한 사용법 및 클로드와의 협업 워크플로우는 `docs/ROBOT_GUIDE.md`를 참고하십시오.
