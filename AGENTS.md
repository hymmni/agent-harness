# Harness Framework: Robot Behavior Intelligence Research

## 🚀 세션 시작 체크리스트
새 세션을 시작할 때 반드시 수행하라:
1. `README.md`를 읽고 프로젝트 구조와 적용 방법을 파악한다.
2. 가상환경이 있는지 확인한다(`venv/`, `.venv/`, `conda` 환경 등). 있으면 해당 환경에서 작업한다.
   - conda: `conda activate <env>` / venv: `source venv/bin/activate`
3. `docs/ARCHITECTURE.md`, `docs/ADR.md`, `docs/private/ENVIRONMENT.md`를 읽고 현재 구조·결정 이력·하드웨어 구성을 파악한다.
4. `git config core.hooksPath`가 `.githooks`가 아니면 사용자에게 알리고 동의를 받아 `python3 .harness/setup.py`를 실행한다.
5. 현재 브랜치의 플랜(`docs/superpowers/plans/`)이 있으면 체크되지 않은 task부터 이어 간다.
6. `continuation_plan.md`가 있으면 읽고 이전 세션의 중단 지점부터 이어서 시작한다.

## 🧪 로봇 연구 프로토콜
- **수정 범위 (Write Scope)**: 모든 소스 코드 수정은 이 작업 레포지토리 내부에서 수행합니다. (단, `references/`는 읽기 전용 — 아래 참조)
- **환경 관리 (Environment)**: 의존성은 프로젝트가 쓰는 파일(`pyproject.toml`, `requirements.txt`, `environment.yml`)에 추가하고, 이 파일들은 레포지토리 루트에서 관리합니다.
- **실행 환경 (Docker)**: `docker-compose.yml`이 있으면 실행·테스트는 `docker compose exec dev <명령>`으로 합니다. 에이전트는 컨테이너 밖에서 작업합니다.
- **참조 범위 (Read Scope)**: `references/` 폴더의 오픈소스 코드를 분석하여 로직을 이식하되, 수정은 절대 금지합니다.
- **출처 표기**: `references/`에서 코드를 가져올 경우 `# From: references/repo_name/file.py`와 같이 주석을 남기십시오.
- **실험 기록**: 의미 있는 변화(알고리즘 교체, 핵심 파라미터 변경) 발생 시 `experiments/` 내에 기록을 남기십시오.

## 📐 아키텍처 & 기술 스택
이 프로젝트의 스택·구조·결정 이력은 `docs/ARCHITECTURE.md`(현재 구조 스냅샷)와 `docs/ADR.md`(결정-이유-트레이드오프 로그)가 단일 진처다. 구조에 영향을 주는 작업 전에는 반드시 두 문서를 먼저 확인하라.

이 문서는 특정 기술 스택을 전제하지 않는다 — 실제 채택 스택(PyTorch/JAX 등), 파이프라인 구조는 프로젝트마다 다르므로 전부 `docs/ARCHITECTURE.md`·`docs/ADR.md`에서 확인하라. 하드웨어 환경(1대/여러 대 PC, GPU 유무, 디바이스 하드코딩 금지 등)은 `docs/private/ENVIRONMENT.md`(git 미추적, 로컬 전용 — 프로젝트 레포가 public일 수 있어 인프라 정보만 분리했다)에서 확인하라. 이 하네스를 새 프로젝트에 처음 적용할 때는 이 세 문서에 해당 프로젝트의 실제 스택·하드웨어를 채워 넣는다.

## 📝 개발 프로세스
- **기본 워크플로우 — 직접 세션 협업**: 새 설계나 구현 방향은 먼저 사용자와 논의해 확정한 뒤 진행한다. 작업 도중 설계 판단이 필요한 지점(접근 방식 선택, 시도가 실패했을 때의 다음 방향, 결과 해석)마다 먼저 확인받고, 사용자 모르게 재설계하지 않는다. 결과가 기대와 다르게 나오면 "안 됐다"로 뭉개지 말고, 무엇을 어떻게 시도했고 왜 그렇게 판단했는지 구체적으로 보고해 사용자가 직접 검증할 수 있게 한다.
- **상세 워크플로우**: 설계·플랜·실행 절차는 `harness` 스킬(`.agents/skills/harness/SKILL.md`)을 따른다.
- **큰 작업 시작 전**: 여러 task짜리 큰 작업을 시작하기 전에 대략적인 토큰 소모 규모(작음/보통/큼)를 사용자에게 알린다. 필요하면 각 에이전트의 공식 수단으로 사용량을 확인해 근거로 제시한다.
- **Commit Message**: Scoped Conventional Commits 사용. **커밋 메시지(제목·본문)는 영어로 작성**한다. 괄호 안에 수정된 모듈 영역(`policy`, `env`, `data`, `config`, `harness` 등 베이스라인 이름이나 모듈)을 명시하고, **제목은 명사형이 아닌 서술형(동사 중심 문장)으로** 작성하며, **반드시 본문에 글머리기호(`-`)를 사용한 멀티라인 상세 설명을 추가**하라. 예시:
  ```
  feat(policy): add diffusion head to transformer backbone

  - replace MLP decoder with DDPM noise predictor to match paper Sec 3.2
  - expose num_diffusion_steps as Hydra config key (default 100)
  - update forward() signature: obs_seq → (action_pred, noise_pred)
  ```
- 작업을 완료할 때마다 `experiments/`에 수정 사항 요약을 작성하십시오.
- **세션 정리**: 작업 단위(태스크/phase/의미 있는 소결)가 끝날 때마다 컨텍스트가 충분히 쌓였는지 스스로 판단해 컨텍스트 정리나 새 세션 시작을 사용자에게 먼저 권장하라.

## 🌿 브랜치와 릴리즈
- 브랜치는 `main`과 `feat|fix|hotfix|refactor|docs|chore/<주제>`만 쓴다. 주제는 소문자, 숫자, `.`, `_`, `-`로 쓴다. main에는 릴리즈 전 코드가 섞일 수 있다.
- 실험은 개인 fork의 `feat/*`에서 한다. fork의 원격 이름은 `personal`로 둔다. 실패한 시도는 `git revert`한다.
- 공유 레포에는 채택한 변경의 최소 diff만 PR로 올린다. 채택하지 않은 브랜치는 fork에 보존하고, 기록에 미채택 결론을 남긴다.
- main 반영은 PR로만 한다. 에이전트가 PR을 만들고(`gh`가 없으면 링크 안내) 사람이 웹에서 일반 병합(merge commit)한다. 에이전트는 main에 직접 커밋이나 병합을 하지 않고, 공유 레포의 main에 push하지 않는다.
- push한 브랜치는 rebase하지 않고 main을 병합해 최신화한다. force push는 `--force-with-lease`도 쓰지 않는다.
- 릴리즈는 main에 `vX.Y.Z` 태그와 GitHub Release로 나눈다. 프로젝트 버전 수정은 태그 전에 PR로 반영한다.
- `hotfix/*`는 배포한 버전만 긴급 수정할 때 쓴다. 해당 태그에서 분기해 수정하고 그 브랜치에 패치 태그를 단 뒤, PR로 main에 합친다. 일반 수정은 `fix/*`를 쓴다.
- 로봇 PC와 공용 학습 서버는 `git checkout vX.Y.Z`로 태그만 쓴다.
- 브랜치와 커밋 규칙은 `.githooks/`가 검사한다. hook을 우회하거나 `core.hooksPath`를 다른 값으로 바꾸지 않는다. 하네스 도입 전에 갈라져 `.githooks/`가 없는 브랜치에서는 main을 병합할 때까지 검사가 동작하지 않는다.

## 📦 작업 산출물
- `scratch/`: git에서 제외한다. 일회용 스크립트는 여기에만 쓰고, 계속 쓸 코드는 `scripts/`나 테스트로 옮긴다.
- `experiments/`: git에서 제외한다. 경로는 `experiments/<브랜치명의 / 를 - 로>/YYYY-MM-DD-주제.md`이고 양식은 `.harness/LOG_TEMPLATE.md`다. 브랜치마다 자기 폴더만 쓴다. 기록을 fork에 남길 때만 `git add -f`로 커밋하고, 공유 레포 PR에는 넣지 않는다.

## 🤖 모델 선택 가이드
작업 복잡도에 맞는 모델 등급을 사용자에게 제안하라. 에이전트는 실행 중인 세션의 모델을 직접 바꿀 수 없으므로, 모델 선택은 세션 시작 전에 사용자가 한다. 등급별 모델 이름은 에이전트마다 다르다.

| 등급 | 적합한 작업 |
|---|---|
| **최고 난이도** | 복합 연구 설계, 장시간 자율 작업, 가장 까다로운 디버깅 |
| **설계·복잡한 구현** | 신규 아키텍처 설계, 복잡한 알고리즘 구현, 다단계 추론이 필요한 작업 |
| **일반 작업** | 일반 코딩, 리팩토링, 대부분의 day-to-day 작업 (기본값) |
| **단순 작업** | 단순 수정, 문서 작성, 빠른 조회성 작업 |

## 🛠️ 유틸리티 명령어
- `python3 .harness/setup.py` # clone마다 한 번 실행: git hook 연결, `.gitignore` 블록과 공유 파일 검사, 설치된 에이전트에 `superpowers` 설치
- `copier update` # 하네스 갱신. 사용자 동의를 받아 브랜치에서 실행하고, 이어서 `python3 .harness/setup.py`를 실행한 뒤 충돌 표시를 해결한다
