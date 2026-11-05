# 설치 옵션: research, main_via_pr

## 의도
하네스를 연구 외의 프로젝트에도 쓴다. 공통 흐름은 main 하나에서 고치고, 프로젝트마다 다른 부분은 copier 설치 질문으로 고른다. 각 프로젝트는 `copier update`로 공통 변경을 받는다.

변형별 장기 브랜치는 쓰지 않는다. 확인한 이유:
- `.copier-answers.yml`이 브랜치를 기록하지 않는다. 변형 브랜치로 설치한 프로젝트에서 `copier update --defaults`를 실행하면 main을 따라가 변형 전용 파일이 지워졌다.
- copier는 레포 전체에서 가장 높은 버전 태그를 고른다. 태그를 브랜치별로 나눌 수 없다.

## 목표
- copier 질문 `research`, `main_via_pr`를 추가한다.
- 연구 전용 규칙과 파일은 `research`를 고를 때만 설치된다.
- main 반영 방식(PR로만 / 로컬 병합 후 push)을 프로젝트마다 고르고, git hook과 규칙이 그 답을 따른다.
- 설치 뒤 `copier update --data research=true`처럼 답을 바꾸면 hook, `setup.py`, `.gitignore` 블록이 따라간다.

## 비목표
- GitHub 서버의 브랜치 보호 자동 설정. public 레포는 README에 웹에서 켜는 방법만 안내한다.
- 프로젝트용 PR·이슈 양식.
- Docker 스캐폴드의 root 실행 문제와 GPU 개수.

## 제약
- 템플릿 레포가 `AGENTS.md`, `.githooks/`, `.harness/`, `.agents/`를 직접 쓴다. 이 파일들에는 jinja를 넣지 않는다.
- 옵션 값은 `.copier-answers.yml`에서 읽는다. hook은 `grep`, `setup.py`는 정규식으로 읽는다(PyYAML 없이). 파일이나 값이 없으면 `research=false`, `main_via_pr=true`다. 템플릿 레포 자신이 이 경우다.
- 에이전트 셸에는 터미널이 없다. 모든 질문은 기본값이 있어 `--defaults`로 끝까지 진행된다.

## 설계

### 질문 (`copier.yml`)
| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `research` | bool | false | 연구용 규칙(실험 기록, 하드웨어 문서, 대용량 파일 제외)을 설치할까요? |
| `main_via_pr` | bool | true | main 반영을 PR로만 할까요? 아니면 로컬에서 병합하고 push합니다. |
| `with_docker` | bool | false | 기존 그대로 |

### 파일 나누기
- 공통: `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.codex/`, `.githooks/`, `.harness/block_dangerous.py`, `.harness/setup.py`, `docs/ADR.md`, `docs/ARCHITECTURE.md`, `docs/README.md`
- research만: `docs/RESEARCH.md`(새 파일), `.harness/LOG_TEMPLATE.md`, `docs/private/ENVIRONMENT.md`. 경로 이름에 `{% if research %}`를 붙인다(Docker와 같은 방식). `docs/private/`는 폴더 이름에 붙인다.
- `docs/ROBOT_GUIDE.md`는 `docs/RESEARCH.md`로 합치고 지운다.
- `docs/ARCHITECTURE.md`, `docs/ADR.md`는 로봇 예시를 빼고 범용 자리표시 문서로 바꾼다. 한 벌만 둔다.

### `AGENTS.md` (공통, jinja 없음)
- 체크리스트 3번은 `ARCHITECTURE.md`, `ADR.md`만 읽는다. 새 항목: "`docs/RESEARCH.md`가 있으면 읽고 그 규칙도 따른다."
- "로봇 연구 프로토콜" 절은 "작업 규칙"으로 바꾼다. 수정 범위, 의존성 파일, Docker 실행, `references/` 읽기 전용과 출처 표기는 남긴다. 실험 기록은 `docs/RESEARCH.md`로 옮긴다.
- 아키텍처 절의 하드웨어·`ENVIRONMENT.md` 문장, 개발 프로세스의 "작업을 완료할 때마다 `experiments/`에 요약" 규칙, 작업 산출물의 `experiments/` 항목은 `docs/RESEARCH.md`로 옮긴다.
- 브랜치와 릴리즈:
  - main 반영: "`.copier-answers.yml`의 `main_via_pr`를 따른다(없으면 true). true면 에이전트가 PR을 만들고 사람이 웹에서 일반 병합한다. false면 사람이 로컬에서 main에 병합하고 push한다. 에이전트는 사용자가 명시적으로 승인한 경우에만 main에 병합하거나 push한다."
  - fork 실험(`personal` 원격, 최소 diff 반영)은 `docs/RESEARCH.md`로 옮긴다. `pre-push`의 `personal` 예외는 그대로 둔다.
  - hotfix: "PR로 main에 합친다" → "main 반영 방식대로 합친다".
  - "로봇 PC와 공용 학습 서버" → "배포·실행 환경은 `git checkout vX.Y.Z`로 태그만 쓴다."

### `docs/RESEARCH.md`
- 에이전트 규칙: 실험 기록(언제, 경로, `.harness/LOG_TEMPLATE.md` 양식, fork에서만 `git add -f`), `docs/private/ENVIRONMENT.md` 읽기와 없을 때 사용자에게 물어 만들기, fork 실험 흐름, 로봇 PC는 태그만.
- 사람용 안내: `ROBOT_GUIDE.md`의 참조·이식 예시, 데이터 심볼릭 링크, 추적 범위.

### `.harness/setup.py`
- `options(root) -> dict[str, bool]`: `.copier-answers.yml`에서 `^(research|main_via_pr): (true|false)$`를 읽는다. 없으면 기본값을 쓴다.
- `.gitignore` 블록
  - 공통: `/.claude/*`, `!/.claude/skills/`, `!/.claude/settings.json`, `/docs/private/`, `/references/`, `/scratch/`, `/continuation_plan.md`, `.env`
  - research: `/experiments/`, `*.pth`, `*.pt`, `*.ckpt`, `*.safetensors`, `*.zarr`, `*.hdf5`, `*.h5`, `wandb/`, `outputs/`
- 공유 파일 검사: 공통 목록에 research일 때 `docs/RESEARCH.md`, `.harness/LOG_TEMPLATE.md`를 더한다.
- 템플릿 레포의 `.gitignore`는 `/experiments/`를 블록 밖에 둔다. 템플릿 개발 기록용이다.

### git hook
- `pre-commit`: 브랜치가 main이고 `.copier-answers.yml`에 `main_via_pr: false`가 있으면 통과한다. 충돌 표시 검사는 두 방식 모두 한다. `pre-merge-commit`은 `pre-commit`을 그대로 쓴다.
- `pre-push`: `main_via_pr: false`면 main push 검사를 건너뛴다.
- `block_dangerous.py`: 바꾸지 않는다. `gh pr merge` 차단은 두 방식 모두 유지한다.

### 기타
- `harness` 스킬 E단계: "main 반영은 `AGENTS.md`의 방식을 따른다." A단계의 `ROBOT_GUIDE` 언급을 뺀다.
- `docs/README.md`: `ROBOT_GUIDE.md`를 빼고 `RESEARCH.md`(research 전용)를 넣는다.
- 템플릿 레포 자신은 답 파일이 없어 `research=false`로 동작한다. 그래서 템플릿 개발에는 실험 기록 규칙이 적용되지 않는다.
- README: 세 질문 설명, 두 main 반영 방식, public 레포의 웹 브랜치 보호 안내, 적용 후 구성에서 research 전용 파일 표시.

## 미리 확인한 것 (copier 9.19.1, 일회용 템플릿)
- 폴더 안 파일 이름의 `{% if research %}`가 동작한다. 다만 파일에만 조건을 걸면 빈 폴더가 남는다(구현 중 테스트로 확인). 그래서 `docs/private/`는 폴더 이름에 조건을 건다.
- 답 파일에 `main_via_pr: true`, `research: false`처럼 한 줄씩 기록된다.
- `copier update --defaults --data research=true`로 연구 파일이 추가되고, `research=false`로 다시 지워진다.
- research를 끄면 `docs/private/ENVIRONMENT.md`도 지워질 수 있다. 연구를 그만두는 경우라 받아들인다. README에 적는다.

## 검증
- copier: research 끄면 연구 파일 없음, 켜면 있음. 답이 `.copier-answers.yml`에 기록됨. `copier update --data research=true`로 연구 파일이 추가됨.
- `setup.py`: 답 파일 없음·research 켬·끔에 따른 블록과 공유 파일 검사.
- hook: `main_via_pr: false`면 main 커밋·병합 커밋·push 허용, true나 답 파일 없음이면 차단.
- 문서: 옮긴 규칙이 `AGENTS.md`와 `docs/RESEARCH.md` 중 맞는 곳에 있음.

## 구현자에게 남긴 것
- `docs/RESEARCH.md`의 문장 구성, 범용 `ARCHITECTURE.md`·`ADR.md` 자리표시 문구.
- 테스트 helper 구성.

## 내가 정한 것 (사용자 확인 필요)
1. `research` 기본값은 false다. 이름이 범용이 되었기 때문이다. 연구실 레포는 설치할 때 true로 답한다.
2. `main_via_pr=false`에서 에이전트는 사용자가 명시적으로 승인한 경우에만 main에 병합하거나 push한다.
3. `ROBOT_GUIDE.md`를 `docs/RESEARCH.md`로 합친다.
4. `references/`, `scratch/`, `docs/private/` 규칙은 공통으로 둔다.
5. `ARCHITECTURE.md`, `ADR.md`는 로봇 예시를 빼고 범용 자리표시로 바꾼다.
