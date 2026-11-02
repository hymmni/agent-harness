# Robot Research Harness Guide

본 가이드는 AI를 활용하여 로봇 행동 지능 프로젝트를 효율적으로 개발하는 방법을 설명합니다.

## 1. 프로젝트 초기화
1. 작업할 베이스라인 레포지토리 루트에서 하네스를 설치합니다. 설치 명령은 템플릿 README를 참고합니다.
2. clone마다 한 번 `python3 scripts/setup.py`를 실행해 git hook을 연결하고 필수 플러그인을 설치합니다.
3. 참고할 논문/오픈소스 코드는 `references/` 폴더에 `git clone` 합니다. (읽기 전용)
4. 실제 하드웨어 구성(PC 몇 대, GPU 유무, 역할 분담 등)을 `docs/private/ENVIRONMENT.md`에 기록합니다. 최초 1회만 채우면 되고, 이후 세션은 그 문서를 참고만 합니다. (이 파일은 git 미추적 — 프로젝트 레포가 public이어도 인프라 정보는 올라가지 않습니다.)
5. 베이스라인 코드와 이식 목표를 에이전트에게 설명하고 작업을 시작합니다.

## 2. 참조 및 이식 워크플로우
- **분석**: "references/에 있는 오픈소스에서 시계열 데이터를 전처리하는 부분을 분석해줘."
- **이식**: "분석한 내용을 바탕으로 베이스라인 코드에 적용해줘. reference 출처는 주석으로 남겨줘."
- **기록**: 수정이 끝나면 `experiments/<브랜치명의 / 를 - 로>/` 폴더에 로그를 작성하게 합니다.

## 3. 유의 사항
- **데이터 관리**: 대용량 데이터와 모델 파일은 `.gitignore`에 의해 제외됩니다. 데이터셋은 심볼릭 링크(ln -s)를 사용하여 외부 경로와 연결하는 것을 권장합니다.
- **일회용 스크립트**: 테스트용 임시 스크립트는 `scratch/`에만 둡니다. 이 폴더는 git에서 제외되므로 나중에 정리할 필요가 없습니다.
- **환경 관리 (Environment)**: 의존성 파일(`pyproject.toml`, `requirements.txt`, `environment.yml`)은 작업 레포 루트에서 관리합니다.
- **git 추적 범위**: 규칙 문서, 에이전트 설정과 스킬, `.githooks/`, `docs/`(단 `docs/private/`는 제외), `scripts/`, `experiments/`는 git으로 추적합니다. `docs/private/`, `references/`, `scratch/`는 로컬 전용입니다. 다르게 하고 싶다면 `.gitignore`에서 해당 규칙을 직접 수정하세요.
