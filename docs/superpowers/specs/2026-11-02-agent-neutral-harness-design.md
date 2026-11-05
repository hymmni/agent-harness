# 에이전트 중립 하네스 설계

## 의도
여러 사람이 각자 브랜치에서 Claude Code, Codex, Antigravity 중 하나로 같은 레포를 수정한다.
규칙·스킬·안전장치는 레포에 두고 공유하고, 어떤 에이전트를 쓸지는 사람별로 정한다.
브랜치 관리는 대부분 에이전트가 하므로, 강제는 GitHub 서버 설정 없이 에이전트 수준까지만 한다.

## 목표
- 어떤 에이전트로 작업해도 같은 규칙을 읽고 같은 스킬을 쓰고 같은 안전장치가 동작한다.
- 공용 파일에 특정 에이전트를 전제한 내용이 없다. 도구별 차이는 얇은 설정 파일과 `.harness/setup.py`의 표에만 둔다.
- main을 보호하고 브랜치·커밋·버전 규칙을 에이전트가 어기기 어렵게 만든다.
- 일회용 스크립트와 실험 기록을 나중에 사람이 뒤져 정리하지 않아도 되게 한다.
- 팀원이 clone 뒤 명령 하나로 같은 환경을 갖춘다.

## 비목표
- GitHub 브랜치 보호, 룰셋, 필수 리뷰 설정
- 실제 연구 프로젝트의 Docker 전환, GUI 패치, 하네스 설치 (이 설계가 끝난 뒤 별도 프로젝트)
- 평가 항목 중 검증 루프(`Verify:`), SessionStart hook
- Codex·Antigravity에서의 `references/` 쓰기 강제

## 안티 목표
- 도구마다 규칙 파일이나 스킬 원본이 따로 생기는 구조
- 안전장치가 조용히 무동작이 되는 구조 (입력을 못 읽으면 통과시키지 않는다)
- GitFlow(`develop`, `release/*`)처럼 이 규모에 맞지 않는 절차

## 사용자가 결정한 사항
- `AGENTS.md`가 단일 원본이고 `CLAUDE.md`는 `@AGENTS.md`로 불러온다. 도구 전용 내용은 넣지 않는다.
- `scripts/scheduler.py`를 삭제한다.
- 설치는 기존 레포 적용 방식만 남긴다. 빈 프로젝트도 같은 방식을 쓴다.
- 에이전트는 Docker 밖에서 작업한다. 컨테이너에는 에이전트를 설치하지 않는다.
- 강제는 지침과 hook까지만 한다.
- `exp/*` 브랜치는 두지 않는다. 실험은 `feat/*` 안에서 하고, 효과가 없으면 병합하지 않는다.
- `develop` 브랜치는 두지 않는다. `main`이 기능을 모으는 역할을 하고, 태그가 배포 버전을 표시한다.
- `hotfix/*`를 둔다.
- 로봇 PC와 공용 학습 서버는 태그만 받아 쓴다.
- 일회용 스크립트 전용 폴더를 둔다.
- 버전과 릴리즈를 구분해 관리한다.
- `scripts/execute.py`를 삭제한다. 플랜은 별도 실행기 없이 에이전트 세션에서 실행한다.
- clone마다 한 번 실행하는 `.harness/setup.py`를 둔다.
- 하네스 스크립트는 `.harness/`에 둔다. `scripts/`는 프로젝트 전용으로 남긴다.
- 필수 외부 의존성은 `superpowers`뿐이다. `mattpocock-skills`, `ponytail`, `i-have-adhd`는 개인 설정으로 둔다.

## 구성

### 규칙
- `AGENTS.md`: 현재 `CLAUDE.md` 내용을 옮기고 다음을 바꾼다.
  - 모델명 표는 난이도 등급(최고 난이도, 설계·복잡한 구현, 일반 작업, 단순 작업)으로 바꾼다.
  - `/compact`, `/clear`는 "컨텍스트 정리 또는 새 세션"으로 바꾼다.
  - `AskUserQuestion`은 "사용자에게 묻는다"로, 사용량 조회 명령은 "각 에이전트의 공식 수단으로 확인한다"로 바꾼다.
  - `execute.py` 안내와 세션 연속 규칙을 지운다. 세션이 끊기면 `continuation_plan.md`나 플랜의 체크박스에서 이어 간다.
  - main 병합 규칙은 아래 브랜치 규칙으로 대체한다.
  - 세션 시작 체크리스트의 `*.state.json` 항목은 "현재 브랜치의 플랜에서 체크되지 않은 task부터 이어 간다"로 바꾼다.
  - 세션 시작 체크리스트에 `git config core.hooksPath`가 `.githooks`가 아니면 사용자에게 알리고 동의를 받아 `python3 .harness/setup.py`를 실행한다는 항목을 추가한다.
  - 의존성은 프로젝트가 쓰는 파일(`pyproject.toml`, `requirements.txt`, `environment.yml`)에 추가한다고 적는다.
  - `docker-compose.yml`이 있으면 실행·테스트는 `docker compose exec dev <명령>`으로 한다고 적는다.
- `CLAUDE.md`: `@AGENTS.md` 한 줄.

### 스킬
- `.agents/skills/harness/SKILL.md`가 원본이다. Codex와 Antigravity가 직접 읽는다.
- `.claude/skills/harness/SKILL.md`는 같은 `name`과 `description`을 두고 원본을 읽으라고만 적은 안내 파일이다.
  심볼릭 링크는 Windows에서 조용히 깨질 수 있어 쓰지 않는다.
- 스킬 본문에서 도구 전용 표현과 `execute.py`, `merge_to_main.py` 설명을 뺀다.
- 플랜은 에이전트 세션에서 `superpowers:executing-plans`나 `superpowers:subagent-driven-development`로 실행하고, 끝난 step은 플랜에서 체크한다.

### 안전장치
- `.harness/block_dangerous.py`는 두 입력 형식을 처리한다.

| 도구 | 설정 파일 | 명령 필드 | 차단 방식 |
|---|---|---|---|
| Claude Code | `.claude/settings.json` | `tool_input.command` | stderr + exit 2 |
| Codex | `.codex/hooks.json` | `tool_input.command` | stderr + exit 2 |
| Antigravity | `.agents/hooks.json` (matcher `run_command`) | `toolCall.args.CommandLine` | stdout `{"decision":"deny","reason":...}` + exit 0 |

- 어느 형식도 아니면 exit 2로 차단한다.
- 차단 패턴에 `--no-verify`, `git commit -n`, `core.hooksPath` 변경, `gh pr merge`를 추가한다. `gh pr merge`는 로컬 `pre-push`를 거치지 않고 서버에서 병합하기 때문이다.
- `block_dangerous.py`의 `# ponytail:` 주석은 일반 주석으로 바꾸고 컨테이너 격리 문구를 지운다.
- 세 설정 파일 모두 git으로 추적한다. 대상 프로젝트의 `.gitignore` 블록에 `!/.claude/settings.json`을 추가한다.
- `references/` 쓰기 차단은 기존 `Edit(/references/**)`를 유지한다. Claude Code에서만 강제되고 나머지는 규칙 문구에 의존한다.

### 환경 설정
- `.harness/setup.py`를 clone마다 한 번 실행한다. 여러 번 실행해도 결과가 같다.
  - `core.hooksPath`를 `.githooks`로 설정한다. 이미 다른 값이 있거나 `.git/hooks`에 사용자 hook이 있으면 바꾸지 않고 경고한다.
  - 설치된 에이전트만 골라 `superpowers`를 사용자 범위로 설치한다. 이미 있으면 건너뛴다.
  - 자동화할 수 없는 신뢰 승인(Claude Code 폴더, Codex `/hooks`)을 안내한다.
- 설치가 실패해도 나머지를 계속 진행하고, 실패한 명령을 출력한 뒤 exit 1로 끝난다.
- 플러그인 설치는 사용자 전역 설정을 바꾸므로, 에이전트가 실행할 때는 사용자에게 먼저 묻는다.

| 도구 | 설치 명령 |
|---|---|
| Claude Code | `claude plugin install superpowers --marketplace anthropics/claude-plugins-official` |
| Codex | `codex plugin add superpowers@openai-curated-remote` |
| Antigravity | `agy plugin install https://github.com/obra/superpowers` |

### 브랜치와 릴리즈
- 브랜치는 `main`과 `feat|fix|hotfix|refactor|docs|chore/<주제>`만 쓴다. main에는 릴리즈 전 코드가 섞일 수 있다.
- 실험은 `feat/*` 안에서 하고, 설정과 결과 기록을 그 브랜치에 커밋한다. 실패한 시도는 `git revert`한다.
- 넣을지 모르는 기능도 `feat/*`로 시작한다. 채택하지 않으면 병합하지 않고 브랜치를 보존하며, 기록에 미채택 결론을 남긴다.
- main 반영은 PR로만 한다. 에이전트가 PR을 만들고(`gh`가 없으면 링크 안내) 사람이 웹에서 일반 병합(merge commit)한다.
- 릴리즈는 main에 `vX.Y.Z` 태그와 GitHub Release로 나눈다. 프로젝트 버전 수정은 태그 전에 PR로 반영한다.
- `hotfix/*`는 배포한 버전만 긴급 수정할 때 쓴다. 해당 태그에서 분기해 수정하고 그 브랜치에 패치 태그를 단 뒤, PR로 main에 합친다. 일반 수정은 `fix/*`를 쓴다.
- 로봇 PC와 공용 학습 서버는 `git checkout vX.Y.Z`로 태그만 쓴다. 이 규칙은 `AGENTS.md`의 지침이며 hook으로 강제하지 않는다.
- `.githooks/`를 추가한다.
  - `pre-commit`: main 직접 커밋과 규칙에 맞지 않는 브랜치 이름을 막는다. detached HEAD와 레포의 첫 커밋은 통과시킨다.
  - `commit-msg`: `타입(스코프): 제목`과 `- ` 본문을 검사한다. 타입은 브랜치 타입에 `test`, `wip`를 더한다. `Merge`와 `Revert` 메시지는 통과시킨다.
  - `pre-push`: `refs/heads/main`으로의 push를 막는다. 원격에 main이 아직 없는 첫 push와 태그 push는 허용한다.
- `scripts/merge_to_main.py`를 삭제한다.

### 작업 산출물
- `scratch/`: git에서 제외한다. 일회용 스크립트는 여기에만 쓰고, 계속 쓸 코드는 `scripts/`나 테스트로 옮긴다.
- `experiments/`: git으로 추적한다. 경로는 `experiments/<브랜치명의 / 를 - 로>/YYYY-MM-DD-주제.md`다.
  브랜치마다 자기 폴더만 쓰므로 충돌하지 않는다.
- `LOG_TEMPLATE.md`에 브랜치, commit, 설정·seed, 데이터 버전, 지표, 판정, 실패한 접근과 이유를 추가한다.
- ADR-002대로 대용량 산출물을 실제로 제외한다: `*.pth`, `*.pt`, `*.ckpt`, `*.safetensors`, `*.zarr/`, `*.hdf5`, `*.h5`, `wandb/`, `outputs/`.

### 설치
- `install.py`
  - 존재 확인 기준을 `AGENTS.md`로 바꾼다.
  - 대상에 `AGENTS.md`나 `CLAUDE.md`가 있으면 덮어쓰지 않고 `*.harness.md`로 남긴다.
  - `--print-gitignore`를 삭제한다.
  - `scratch/` 디렉토리를 만든다.
  - hook 연결은 `setup.py`에 맡기고, 완료 메시지에서 `python3 .harness/setup.py` 실행을 안내한다.
- `.gitignore` 블록: `/experiments/`를 빼고 `/scratch/`, `/AGENTS.harness.md`, `!/.claude/settings.json`, 대용량 패턴을 넣는다.
- README는 적용 방법을 하나로 합치고 빈 프로젝트는 `git init` 후 같은 명령을 쓰게 한다. 빈 상태 시작 명령은 제거한다. 설치한 사람과 팀원은 clone마다 `python3 .harness/setup.py`를 실행한다고 적는다.

### Docker
- 공용 파일에서 에이전트 관련 내용을 뺀다: `~/.claude` 마운트, `HOME` 덮어쓰기, Node feature, CLI 설치, `onCreateCommand`, `DOCKER.md`의 관련 설명.
- 개발 환경 기능(GPU, GUI, devcontainer)과 non-root 사용자는 유지한다.
- Dockerfile의 다른 프로젝트 참조 주석을 지운다.

## 구현 시 확인할 것
권한을 우회하지 않는 실제 세션으로 확인한다.
- `claude -p`에서 `@AGENTS.md`가 불러와지는가
- `codex exec -`, `agy -p`가 stdin 프롬프트를 받고 `AGENTS.md`를 읽는가
- 세 도구가 `harness` 스킬을 찾는가
- Antigravity와 Codex에서 hook이 실제로 차단하는가
- 빈 프로젝트와 기존 프로젝트 양쪽에 설치되는가
- `setup.py`가 새 clone에서 hook을 연결하고 세 도구에 `superpowers`를 설치하는가
- Codex 설치 명령의 플러그인 이름이 맞는가
- 에이전트가 git hook을 통과하는 브랜치와 커밋을 만드는가

## 2026-11-03 변경
독립 검토와 실제 대상 프로젝트 확인 뒤 다음을 바꿨다. 위 내용과 다르면 이 절이 우선한다.

- 실험은 `feat/*`의 커밋이 아니라 개인 fork에서 한다. 첫 적용 대상의 `CONTRIBUTING.md`가 fork 방식이기 때문이다. `experiments/`는 git에서 제외하고, 양식은 새 clone에도 전달되도록 `.harness/LOG_TEMPLATE.md`로 옮겼다.
- `pre-push`는 원격 이름이 `personal`일 때만 main push를 허용한다. `origin`만 막으면 공유 레포를 `upstream`으로 둔 clone에서 차단이 조용히 사라지므로, 예외를 하나만 두는 쪽을 택했다.
- `.gitignore` 충돌 검사는 `setup.py`에 둔다. 설치 직후와 새 clone 양쪽에서 같은 검사가 돌아야 하기 때문이다.
- 도입 전 브랜치의 hook 공백은 `.git/hooks` 연결 파일로 막지 않고 문서로 남긴다. 연결 파일은 main을 병합하지 않은 fork 실험 브랜치의 커밋까지 막아 "fork 안에서는 제약 없이"라는 약속과 충돌한다. main에 체크아웃한 동안의 보호는 그대로이고, 공백은 그런 브랜치에서 동작할 때로 한정된다.

### 설치 방식: copier
이미 설치한 프로젝트에 템플릿 갱신을 반영할 수 있도록 `install.py`를 지우고 copier로 바꿨다.

- 레포 루트가 템플릿이다. 템플릿 레포 자신도 같은 하네스로 개발하므로 하위 폴더로 옮기지 않았다. 템플릿 개발용 파일은 `_exclude`로 빼고, 루트 목록 테스트로 새 파일의 유출을 막는다.
- 프로젝트가 채워 쓰는 `docs/ADR.md`, `docs/ARCHITECTURE.md`, `docs/private/ENVIRONMENT.md`는 `_skip_if_exists`로 갱신하지 않는다.
- copier는 기존 `.gitignore`에 덧붙이지 못하므로 관리 블록은 `setup.py`가 맞춘다. copier 작업(`_tasks`)은 `--trust`가 필요해 쓰지 않았다.
- Docker 스캐폴드는 `with_docker` 질문과 조건부 파일 이름으로 고른다.
- 갱신의 충돌 표시가 커밋되지 않도록 `pre-commit`이 막는다.
- 기존 `*.harness.md` 병합 안내는 copier의 덮어쓰기 확인으로 대신한다.

## 구현자에게 맡기는 것
- 파일 내부 구조, 함수 이름, 커밋 분할
- 위험 명령 정규식의 구체적인 형태
- `AGENTS.md` 문구

## 전제
- 아직 커밋되지 않은 이전 수정이 `main` 작업 트리에 있다. 구현 전에 브랜치로 옮겨 커밋해야 한다.
- 빈 상태 시작 경로 수정과 `--print-gitignore` 문구는 이 설계로 사라진다.
