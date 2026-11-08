# Agent Harness

이 저장소는 코딩 에이전트와 함께 작업하는 프로젝트에 설치하는 **하네스 템플릿**입니다. 프로젝트 레포에 적용하면 Claude Code, Codex, Antigravity 중 어떤 에이전트를 쓰든 같은 규칙과 스킬, 안전장치로 구조화된 워크플로우(탐색 → 논의 → 플랜 작성 → 실행)를 따를 수 있습니다. 로봇 연구용 규칙(실험 기록, 하드웨어 문서, 대용량 파일 제외)은 설치할 때 고릅니다.

## 사전 준비

- Python 3
- 사용할 에이전트
- 설치하거나 갱신하는 사람만: [copier](https://copier.readthedocs.io/) 9 이상 (`pipx install copier` 또는 `uv tool install copier`). 팀원에게는 필요 없습니다.

## 적용 방법

**적용할 프로젝트 레포 루트에서** 실행합니다. 빈 프로젝트는 먼저 `mkdir <이름> && cd <이름> && git init -b main`을 실행합니다. 기존 프로젝트는 먼저 `chore/add-harness` 같은 브랜치를 만들고, 설치 결과를 그 브랜치에 커밋한 뒤 평소 방식대로 main에 합칩니다.

```bash
copier copy gh:hymmni/agent-harness .
python3 .harness/setup.py
```

- copier가 세 가지를 묻습니다. 답은 `.copier-answers.yml`에 남고, hook과 `setup.py`가 이 답을 따릅니다.

  | 질문 | 기본값 | 고르면 |
  |---|---|---|
  | `research` | 아니오 | `docs/RESEARCH.md`, `.harness/LOG_TEMPLATE.md`, `docs/private/ENVIRONMENT.md`를 설치하고, `.gitignore`에 `experiments/`와 대용량 파일(`*.pth`, `*.ckpt`, `wandb/` 등)을 추가합니다. |
  | `main_via_pr` | 예 | 예: main 반영은 PR로만 하고, hook이 main 커밋·병합·push를 막습니다. release-please가 릴리즈 PR을 엽니다. 아니오: 사람이 로컬에서 main에 병합하고 push하며, hook은 main을 막지 않습니다. 버전 태그는 사람이 직접 답니다. |
  | `with_docker` | 아니오 | Docker 개발 환경 스캐폴드를 설치합니다. |

- 이미 있는 파일과 겹치면 copier가 덮어쓸지 묻습니다. 덮어쓰지 않은 파일(예: 기존 `AGENTS.md`)에는 하네스 내용을 직접 병합합니다. 이 질문에 답할 터미널이 없으면 copier가 중간에 멈춰 일부 파일만 복사되므로, 터미널에서 직접 실행합니다.
- `docs/ADR.md`, `docs/ARCHITECTURE.md`, `docs/private/ENVIRONMENT.md`는 프로젝트가 채워 쓰는 문서라 처음 한 번만 만들고 갱신하지 않습니다. 설치한 뒤 에이전트에게 두 `docs/` 문서를 채워 달라고 합니다. 문서에 "자리표시"가 남아 있으면 에이전트도 세션을 시작할 때 먼저 채우자고 제안합니다.
- `.copier-answers.yml`은 갱신에 필요하므로 함께 커밋하고, 직접 수정하지 않습니다.
- `install.py`로 설치했던 프로젝트도 같은 명령으로 다시 적용합니다. 겹치는 파일은 덮어쓰고 차이를 검토합니다.

`setup.py`는 `.gitignore`에 하네스 블록을 추가하고, 공유 파일이 `.gitignore`에 제외되어 있으면 알립니다. 알리면 그 규칙을 지운 뒤 다시 실행합니다. 지우기 전에 커밋하면 새 clone에 규칙과 안전장치가 전달되지 않습니다. 블록 안은 `setup.py`가 덮어쓰므로 프로젝트 규칙은 블록 밖에 둡니다.

`.gitignore`에서 풀린 경로는 다음 pull 때 팀원의 같은 이름 로컬 파일과 충돌할 수 있으니, 병합 전에 백업을 공지합니다.

### 하네스 갱신

템플릿이 바뀌면 브랜치에서 갱신합니다. 작업 트리에 커밋하지 않은 변경이 없어야 실행됩니다.

```bash
git switch -c chore/update-harness
copier update
python3 .harness/setup.py
```

copier는 템플릿의 최신 `vX.Y.Z` 태그를 가져오고, 태그가 없으면 최신 커밋을 씁니다. 프로젝트에서 고친 내용은 보존됩니다. 같은 줄을 양쪽에서 고쳤으면 `<<<<<<<` 충돌 표시가 남고, 해결하기 전에는 `pre-commit`이 커밋을 막습니다.

설치할 때 고른 답은 갱신하면서 바꿉니다. 예를 들어 `copier update --data research=true`는 연구 파일을 추가하고, 이어서 `setup.py`가 `.gitignore` 블록을 맞춥니다. `research=false`로 바꾸면 연구 파일이 지워지고, 로컬의 `docs/private/ENVIRONMENT.md`도 지워질 수 있습니다.

### 팀원이 clone한 뒤

clone마다 한 번 실행합니다. 여러 번 실행해도 결과가 같습니다.

```bash
python3 .harness/setup.py
```

- git hook을 `.githooks/`에 연결합니다. 다른 hook이 이미 있으면 바꾸지 않고 알려 줍니다.
- `.gitignore`의 하네스 블록을 최신 내용으로 맞추고, 공유 파일이 있고 제외되지 않았는지 검사합니다.
- 설치된 에이전트에 `superpowers` 플러그인을 설치합니다. 하네스의 필수 플러그인은 이것뿐이고, 나머지는 개인 선택입니다.
  - Claude Code: 이 프로젝트 범위로 설치합니다. `.claude/settings.json`에 켜져 있어 팀원에게 전달되지만, 플러그인 내려받기는 clone마다 해야 합니다. 다른 프로젝트에는 설치되지 않습니다.
  - Codex, Antigravity: 프로젝트 범위 설치를 지원하지 않아 사용자 범위로 설치합니다.

다음 승인은 자동화할 수 없어 직접 합니다.

- Claude Code: 첫 실행 때 폴더 신뢰를 승인합니다.
- Codex: `/hooks`에서 이 레포의 hook을 승인합니다. 승인 전에는 위험 명령이 차단되지 않습니다.

에이전트별로 알아 둘 점입니다.

- Codex는 로그인한 뒤에 `setup.py`를 실행합니다. 플러그인 목록을 받으려면 로그인이 필요합니다.
- `codex exec`의 `workspace-write` 샌드박스는 `.git`에 쓰지 못해 브랜치를 만들 수 없습니다.
- `agy -p`는 비대화형이라 셸 명령을 승인할 수 없습니다. 브랜치와 커밋 작업은 대화형 세션에서 합니다.

`research`로 설치했다면 `docs/private/ENVIRONMENT.md`는 git으로 전달되지 않으므로 clone마다 채웁니다.

### 하네스 제거

제거 명령은 없으니 브랜치에서 직접 지웁니다. 프로젝트가 채운 `docs/ARCHITECTURE.md`, `docs/ADR.md`나 직접 고쳐 쓰는 `requirements.txt`는 남겨도 됩니다.

1. 하네스가 설치한 경로를 지웁니다. 설치 때 고른 답에 따라 일부만 있습니다.
   - 공통: `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, `.codex/`, `.githooks/`, `.harness/`, `.copier-answers.yml`, `docs/`의 `README.md`·`ARCHITECTURE.md`·`ADR.md`
   - `research`: `docs/RESEARCH.md`, `docs/private/ENVIRONMENT.md`
   - `main_via_pr`: `.github/workflows/release.yml`, `.github/release-please-config.json`, `.github/.release-please-manifest.json`
   - `with_docker`: `DOCKER.md`, `docker-compose.yml`, `docker-compose.gpu.yml`, `docker/`, `.devcontainer/`, `.env.example`, `requirements.txt`
2. `.gitignore`에서 `# >>> harness gitignore (managed) >>>`부터 `# <<< harness gitignore (managed) <<<`까지 지웁니다.
3. clone마다 `git config --unset core.hooksPath`로 git hook 연결을 풉니다. 에이전트에게는 이 명령이 차단되므로 사람이 실행합니다.
4. Claude Code의 `superpowers`는 `claude plugin uninstall superpowers --scope project`로 지웁니다. Codex와 Antigravity에는 사용자 범위로 설치되어 다른 프로젝트도 쓰므로 그대로 둡니다.

### 적용 후 구성

```
AGENTS.md        # 규칙의 단일 원본 — git 추적
CLAUDE.md        # AGENTS.md를 불러오는 한 줄 — git 추적
.agents/         # 공용 스킬, Antigravity hook — git 추적
.claude/         # Claude Code 설정과 스킬 안내 파일 (settings.json, skills/만 git 추적)
.codex/          # Codex hook — git 추적
.githooks/       # 브랜치·커밋 규칙 — git 추적
docs/            # 구조와 결정 기록 (ARCHITECTURE, ADR) — git 추적
.harness/        # 설정과 안전장치 스크립트 — git 추적
references/      # 외부 오픈소스를 분석용으로 Clone (Read-only) — git 미추적
scratch/         # 일회용 스크립트 — git 미추적
.gitignore       # 하네스 산출물 제외 규칙 (setup.py가 관리하는 블록)
.copier-answers.yml  # 설치한 템플릿 버전과 답변 — git 추적, 직접 수정 금지
```

`research`를 고르면 다음이 더해집니다.

```
docs/RESEARCH.md          # 연구 규칙과 안내 — git 추적
docs/private/             # PC/GPU 등 로컬 인프라 정보 (ENVIRONMENT.md) — git 미추적
.harness/LOG_TEMPLATE.md  # 실험 기록 양식 — git 추적
experiments/              # 브랜치별 실험 기록 — git 미추적, fork에만 git add -f
```

Docker 스캐폴드를 고르면 `DOCKER.md`, `docker-compose*.yml`, `docker/`, `.devcontainer/`, `.env.example`, `requirements.txt`가 함께 생깁니다.

대상 프로젝트가 public 레포일 수 있어 인프라 정보(`docs/private/`)는 추적하지 않습니다. 워크플로우 실행 시 `docs/superpowers/plans/`에 플랜(`.md`)이 쌓입니다.

## 브랜치와 릴리즈

GitHub Flow를 따릅니다. `main`과 `feat|fix|refactor|docs|chore/<주제>` 브랜치만 쓰고, 브랜치에 main을 병합해 테스트한 뒤 main에 합칩니다. 그래서 main은 언제든 태그를 달 수 있습니다. 사람들에게 새 버전으로 올리라고 알릴 때만 main에 `vX.Y.Z` 태그를 답니다. 옛 버전을 따로 고치는 브랜치는 두지 않습니다. main 반영 방식은 설치 때 고른 `main_via_pr`를 따릅니다. 자세한 규칙은 `AGENTS.md`를 참고하십시오.

- **`main_via_pr: true`**: 에이전트가 PR을 만들고 사람이 웹에서 일반 병합합니다. hook이 main 커밋·병합·push를 막습니다. 병합할 때마다 release-please가 릴리즈 PR을 열거나 갱신하고, 릴리즈 PR을 병합하면 태그와 GitHub Release가 생깁니다.
- **`main_via_pr: false`**: 사람이 로컬에서 `git merge --no-ff <브랜치>`로 main에 병합하고 push합니다. hook은 main을 막지 않습니다. 새 버전은 사람이 버전 표기를 고쳐 main에 반영하고 `git tag -a vX.Y.Z -m "<바뀐 점>"`으로 태그를 달아 push합니다. GitHub Release는 필요할 때만 만듭니다.

`main_via_pr: true`로 설치하면 `.github/`에 릴리즈 PR 워크플로와 설정이 생깁니다.

- 레포 관리자가 Settings → Actions → General에서 "Allow GitHub Actions to create and approve pull requests"를 켜야 릴리즈 PR이 열립니다. 조직 레포는 조직 설정에서 먼저 허용해야 할 수 있습니다.
- 첫 릴리즈는 `0.1.0`입니다. 이미 버전을 쓰던 레포라면 `.github/.release-please-manifest.json`의 `"0.0.0"`을 현재 버전으로 바꿉니다.
- 버전은 커밋 타입으로 정합니다. 제목에 `!`가 있으면 major, `feat`가 있으면 minor, 그 밖에는 patch를 올립니다. 1.0.0 전에는 `!`도 minor만 올립니다. 1.0.0으로 올릴 때는 커밋 본문에 `Release-As: 1.0.0` 줄을 넣습니다. 릴리즈 노트는 병합된 PR 목록이라 `chore`만 병합돼도 릴리즈 PR이 열릴 수 있습니다. 내보낼지는 릴리즈 PR을 병합할지로 정합니다.
- Python 프로젝트는 `.github/release-please-config.json`의 `"release-type"`을 `"python"`으로 바꾸면 `pyproject.toml`의 버전도 함께 올립니다. 이 수정은 `copier update` 뒤에도 남습니다.

두 방식 모두 에이전트는 main에 커밋·병합·push하지 않습니다. git hook은 사람과 에이전트를 구분하지 못하므로, 에이전트의 명령에만 걸리는 위험 명령 차단 스크립트가 이런 명령을 막습니다. 필요하면 사람이 터미널에서 직접 실행합니다. 차단 스크립트는 명령 문자열을 순서대로 따라가며 `cd`, `git -C`, 브랜치 전환을 반영해 대상 레포의 브랜치를 판단합니다. 스크립트를 거쳐 실행하거나, 서브셸 안에서 `cd`하거나, 변수로 만든 경로는 못 따라갑니다.

하네스의 강제는 에이전트 지침과 로컬 hook까지입니다. GitHub 서버의 브랜치 보호는 설정하지 않습니다. public 레포라면 무료 플랜에서도 레포의 Settings → Rules에서 main에 PR 필수 룰셋을 켤 수 있고, 그러면 서버가 직접 막습니다. private 레포는 유료 플랜이 필요합니다.

`research`로 설치했다면 실험은 개인 fork에서 하고, 공유 레포에는 채택한 변경의 최소 diff만 올립니다. fork의 원격 이름을 `personal`로 두면 fork의 main은 push 차단에서 빠집니다.

hook 파일은 브랜치마다 따라다니므로, 도입 전에 갈라진 브랜치에서는 main을 병합할 때까지 브랜치·커밋 검사와 push 차단이 동작하지 않습니다. 팀원은 그런 브랜치를 main에 합치기 전에 main을 병합합니다.

`references/` 쓰기 차단은 Claude Code에서만 강제되고, 다른 에이전트는 `AGENTS.md`의 규칙에 의존합니다.

### 여러 기능을 동시에 작업하기 (선택)

기능을 동시에 개발하려면 브랜치마다 `git worktree`로 폴더를 따로 만들 수 있습니다. 한 번에 하나만 작업한다면 필요 없습니다.

    git worktree add ../<레포>-<주제> -b feat/<주제>

- git hook과 위험 명령 차단 스크립트는 worktree에서도 동작합니다. `.githooks/`가 추적되는 파일이라 새 폴더에도 있고, 브랜치 이름과 커밋 메시지 검사가 그대로 걸립니다. 단 하네스 도입 전에 갈라진 브랜치는 `.githooks/`가 없어 검사가 없습니다.
- Claude Code의 `references/` 수정 차단(Edit 도구)도 worktree에서 동작합니다. worktree 안의 링크 경로와 원래 폴더의 절대 경로 모두 거부되는 것을 확인했습니다. Bash로 파일에 쓰는 명령은 이 규칙의 대상이 아닙니다.
- 폴더는 레포 밖에 두면 `.gitignore`를 건드릴 필요가 없습니다.
- git이 추적하지 않는 파일(`references/`, `docs/private/`, 데이터 링크, `.env`)은 새 폴더에 없습니다. 필요한 것은 폴더마다 링크하거나 복사합니다.
- `pip install -e`는 한 폴더만 가리킵니다. worktree에서 테스트하면 원래 폴더의 코드를 import할 수 있으니, worktree마다 가상환경을 만들어 설치하거나 `python -c "import 패키지; print(패키지.__file__)"`로 경로를 확인합니다.
- 같은 브랜치는 두 폴더에서 동시에 체크아웃할 수 없습니다. main도 마찬가지이므로 `main_via_pr: false`에서 병합할 폴더(원래 폴더)는 main으로 비워 둡니다.
- 다 쓴 폴더는 `git worktree remove <폴더>`로 지웁니다.

## 시작하기

에이전트 협업 워크플로우는 `harness` 스킬(`.agents/skills/harness/SKILL.md`)에, 연구용 사용법은 `research`로 설치한 프로젝트의 `docs/RESEARCH.md`에 있습니다.

## 문제 보고

하네스의 버그나 개선 제안은 이 레포의 [Issues](https://github.com/hymmni/agent-harness/issues/new/choose)에 양식으로 올립니다. 이 레포는 public이므로 프로젝트 이름, 코드, 파일 경로, 인프라 정보는 적지 않습니다. 설치된 프로젝트의 에이전트도 `AGENTS.md`의 규칙에 따라, 사용자가 동의하면 같은 방식으로 이슈를 올립니다.

설치된 프로젝트에서는 하네스 파일을 직접 고치지 않습니다. 프로젝트에서 고친 내용은 `copier update` 뒤에도 남아 템플릿의 수정과 겹치기 때문입니다. 버그를 만나면 hook이나 차단 스크립트를 끄지 않는 방법으로 피해 가고(막힌 명령은 사람이 터미널에서 실행), 이슈를 올린 뒤 고친 버전을 `copier update`로 받습니다.

## 템플릿 개발

레포 루트가 copier 템플릿입니다. `copier.yml`의 `_exclude`에 있는 README, `tests/`, `docs/superpowers/`, `.github/`의 이슈 양식과 릴리즈 설정 같은 템플릿 개발용 파일은 프로젝트로 복사되지 않습니다. 루트에 새 파일을 추가하면 `tests/test_copier.py`가 실패하니, 복사할지 `_exclude`에 넣을지 정합니다. 이름에 `{% if with_docker %}`, `{% if research %}`, `{% if main_via_pr %}`가 붙은 파일과 폴더는 그 질문에 "예"라고 답했을 때만 만들어집니다. 템플릿 레포 자신에는 `.copier-answers.yml`이 없어 `research=false`, `main_via_pr=true`로 동작합니다.

테스트에는 copier와 pytest가 필요합니다.

```bash
python3 -m pip install copier pytest
python3 -m pytest -q tests
```

템플릿 릴리즈는 [release-please](https://github.com/googleapis/release-please)가 관리합니다. PR이 main에 병합되면 GitHub Actions가 릴리즈 PR을 열거나 갱신합니다. 릴리즈 PR에는 다음 버전과 `CHANGELOG.md`가 들어 있고, 이것을 병합하면 `vX.Y.Z` 태그와 GitHub Release가 만들어집니다. 각 프로젝트는 `copier update`로 그 버전을 받습니다.

- 버전과 릴리즈 노트 규칙은 "브랜치와 릴리즈"의 `main_via_pr: true` 프로젝트와 같습니다. 릴리즈 노트를 커밋이 아니라 병합된 PR로 만드는 이유는, 병합 커밋 본문에 PR 제목이 들어가 커밋 기준이면 항목이 두 번씩 나오기 때문입니다.
- 여러 PR을 모았다가 릴리즈 PR 하나로 내보낼 수 있습니다. 릴리즈 PR이 열려 있으면 아직 프로젝트에 나가지 않은 변경이 있다는 뜻입니다.
- 태그를 손으로 달지 않습니다. `version.txt`와 `.release-please-manifest.json`은 release-please가 고칩니다.

커밋하지 않은 변경이 있는 로컬 작업본으로 설치하면 copier가 임시 커밋 번호를 기록해, 그 프로젝트는 나중에 `copier update`를 할 수 없습니다. 실제 설치는 `gh:` 주소로 합니다.
