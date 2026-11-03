#!/usr/bin/env python3
"""
Harness 부트스트랩 설치기 — 작업 레포 안에 클론한 템플릿을 적용하고 스스로 정리한다.

기존 프로젝트에 적용 (단 두 단계):

    cd /path/to/your-project           # 적용 대상 프로젝트 루트
    git clone <template-url> harness   # 작업 레포 "안에" harness/ 로 클론
    python3 harness/install.py         # 이 한 줄로 끝

이 스크립트가 하는 일:
    1. 클론(harness/)의 harness 파일을 프로젝트 루트로 복사 (없는 파일만, 기존 파일·.git 보존)
    2. 기존 .gitignore 에 harness 규칙을 멱등하게 추가
    3. harness 디렉토리(experiments/ references/ scratch/) 생성
    4. 클론 디렉토리(harness/)를 통째로 삭제해 스스로 정리

빈 프로젝트는 `git init -b main` 후 같은 방법으로 적용한다. git hook 연결, 공유 파일 검사,
플러그인 설치는 clone마다 필요하므로 설치 후 `python3 .harness/setup.py`로 한다.

기존 파일을 절대 덮어쓰지 않는다(비파괴). 기존 AGENTS.md 나 CLAUDE.md 가 있으면 harness
버전을 *.harness.md 로 남겨 수동 병합하게 한다.

Docker/devcontainer 개발 환경(docker-optional/)은 기본적으로 설치하지 않는다 — 대화형
실행 시 물어보고, `--with-docker`로 강제 설치하거나 `--without-docker`(또는 `--yes`만 주고
아무 지정 안 함)로 건너뛸 수 있다. 설치되는 파일의 `docker-compose.yml` image 이름, devcontainer
이름은 대상 디렉터리 이름으로 자동 치환된다. 왜 이런 구조인지는 설치된 DOCKER.md 참고.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

CLONE_ROOT = Path(__file__).resolve().parent   # 클론된 템플릿 루트 (= harness/)
TARGET_ROOT = CLONE_ROOT.parent                # 적용 대상 프로젝트 루트

# Docker/devcontainer 스캐폴드는 옵션이라 기본 copy_tree 대상에서 빼고 별도로 다룬다
# (docker-optional/ 아래는 대상 프로젝트 루트 레이아웃을 그대로 미러링함).
DOCKER_SRC_DIRNAME = "docker-optional"
PROJECT_NAME_PLACEHOLDER = "__PROJECT_NAME__"
# docker-optional/ 안에서 플레이스홀더 치환이 필요한 파일들 (docker-optional 기준 상대경로)
DOCKER_TEMPLATED_FILES = {"docker-compose.yml", ".devcontainer/devcontainer.json"}

# --- .gitignore 블록 (대상 프로젝트 전용). 설치 시 대상의 .gitignore 에 append 되어
#     harness 도구가 그 프로젝트 이력을 오염시키지 않게 한다.
#     주의: 이 블록은 '대상 프로젝트용'이다. 이 템플릿 레포 자신의 .gitignore 와는 별개이며
#     (템플릿 레포는 .harness/ docs/ 등 harness 소스를 추적해야 하므로), 둘을 동일시하지 마라. ---
GITIGNORE_BEGIN = "# >>> harness gitignore (managed) >>>"
GITIGNORE_END = "# <<< harness gitignore (managed) <<<"
GITIGNORE_BLOCK = """\
/CLAUDE.harness.md
/AGENTS.harness.md
/.claude/*
!/.claude/skills/
!/.claude/settings.json
/docs/private/
/experiments/
/references/
/scratch/
/continuation_plan.md
*.pth
*.pt
*.ckpt
*.safetensors
*.zarr
*.hdf5
*.h5
wandb/
outputs/
"""

# 어느 깊이에서든 복사하지 않을 항목 (git 메타, 캐시, 이 템플릿 자체의 설계 문서)
ALWAYS_SKIP = {".git", "__pycache__", ".pytest_cache", ".DS_Store", "superpowers"}
# 클론 최상위에서만 제외할 항목 (설치 도구 자체 + 템플릿 전용 테스트 + README, .gitignore는
# append로 처리, docker-optional/은 옵션이라 install_docker()가 별도로 처리)
TOP_EXCLUDE = {"install.py", "README.md", ".gitignore", "tests", DOCKER_SRC_DIRNAME}
HARNESS_DIRS = ("experiments", "references", "scratch")
# 대상에 이미 있으면 덮어쓰지 않고 *.harness.md 로 남기는 규칙 파일
CONFLICT_FILES = ("AGENTS.md", "CLAUDE.md")


def slugify_project_name(name: str) -> str:
    """디렉터리 이름을 docker image 이름으로 쓸 수 있는 형태로 정리."""
    slug = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-")
    return slug or "project"


def copy_docker_tree(src: Path, dst: Path, project_slug: str, rel: Path = Path(".")) -> int:
    """docker-optional/ 내용을 대상 루트로 복사. 지정된 파일만 __PROJECT_NAME__을 치환.
    기존 파일은 건너뛴다(비파괴). 복사한 파일 수를 반환."""
    count = 0
    for item in src.iterdir():
        if item.name in ALWAYS_SKIP:
            continue
        rel_path = rel / item.name
        target = dst / item.name
        if item.is_dir():
            target.mkdir(exist_ok=True)
            count += copy_docker_tree(item, target, project_slug, rel_path)
        elif not target.exists():
            if rel_path.as_posix() in DOCKER_TEMPLATED_FILES:
                content = item.read_text(encoding="utf-8")
                target.write_text(
                    content.replace(PROJECT_NAME_PLACEHOLDER, project_slug), encoding="utf-8"
                )
            else:
                shutil.copy2(item, target)
            count += 1
    return count


def install_docker(assume_yes: bool, want_docker) -> None:
    """want_docker: True/False로 명시되면 그대로 따르고, None이면 대화형으로 묻는다
    (단, --yes로 비대화형일 땐 명시가 없으면 기본 미설치)."""
    docker_src = CLONE_ROOT / DOCKER_SRC_DIRNAME
    if not docker_src.exists():
        return
    if want_docker is None:
        if assume_yes:
            return
        want_docker = confirm("  Docker/devcontainer 개발 환경 스캐폴드도 같이 설치할까요?", False)
    if not want_docker:
        return
    project_slug = slugify_project_name(TARGET_ROOT.name)
    n = copy_docker_tree(docker_src, TARGET_ROOT, project_slug)
    print(f"  Docker 스캐폴드 설치: {n}개 파일 (image: {project_slug}/dev, DOCKER.md 참고)")
    ensure_gitignore_line(TARGET_ROOT / ".gitignore", ".env")


def ensure_gitignore_line(target: Path, line: str) -> None:
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    if any(l.strip() == line for l in existing.splitlines()):
        return
    sep = "" if existing == "" or existing.endswith("\n") else "\n"
    target.write_text(existing + sep + line + "\n", encoding="utf-8")
    print(f"  .gitignore: {line} 추가")


def gitignore_text() -> str:
    return f"{GITIGNORE_BEGIN}\n{GITIGNORE_BLOCK}{GITIGNORE_END}\n"


def install_gitignore(target: Path) -> str:
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    block = re.compile(f"{re.escape(GITIGNORE_BEGIN)}.*?{re.escape(GITIGNORE_END)}\n?", re.DOTALL)
    if block.search(existing):
        updated = block.sub(lambda _: gitignore_text(), existing, count=1)
        if updated == existing:
            return ".gitignore: 이미 harness 블록 존재 (변경 없음)"
        target.write_text(updated, encoding="utf-8")
        return ".gitignore: harness 블록을 최신 내용으로 교체"
    sep = "" if existing == "" or existing.endswith("\n") else "\n"
    gap = "\n" if existing.strip() else ""
    target.write_text(existing + sep + gap + gitignore_text(), encoding="utf-8")
    return ".gitignore: harness 블록 추가" if existing else ".gitignore: 생성 + harness 블록 추가"


def copy_tree(src: Path, dst: Path, skipped: list, top: bool = True) -> int:
    """src 내용을 dst로 복사. 기존 파일은 건너뛰고(비파괴) skipped에 기록한다. 복사한 파일 수를 반환."""
    count = 0
    for item in src.iterdir():
        if item.name in ALWAYS_SKIP or (top and item.name in TOP_EXCLUDE):
            continue
        target = dst / item.name
        if item.is_dir():
            target.mkdir(exist_ok=True)
            count += copy_tree(item, target, skipped, top=False)
        elif target.exists():
            skipped.append(target.relative_to(TARGET_ROOT).as_posix())
        else:
            shutil.copy2(item, target)
            count += 1
    return count


def confirm(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    try:
        return input(f"{prompt} [y/n] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def run_install(assume_yes: bool, want_docker=None) -> int:
    # 끝에 CLONE_ROOT를 지우므로, 이름이 다른 템플릿 작업본에서 잘못 실행해도 지우지 않게 막는다.
    if CLONE_ROOT.name != "harness" or not (CLONE_ROOT / "AGENTS.md").exists():
        print("  ERROR: 이 스크립트는 프로젝트 안에 harness/로 clone한 템플릿에서 실행해야 합니다.")
        print("         cd <your-project> && git clone <url> harness && python3 harness/install.py")
        return 1

    print(f"\n  Harness 설치")
    print(f"    from (clone) : {CLONE_ROOT}")
    print(f"    into (target): {TARGET_ROOT}")
    if not confirm("  위 target 에 harness를 설치하고 clone을 삭제합니다. 계속할까요?", assume_yes):
        print("  중단됨.")
        return 1

    # 규칙 파일 충돌 시 harness 버전을 보존 (clone 삭제 후에도 병합 가능하도록)
    conflicts = [name for name in CONFLICT_FILES if (TARGET_ROOT / name).exists()]
    for name in conflicts:
        shutil.copy2(CLONE_ROOT / name, TARGET_ROOT / f"{Path(name).stem}.harness.md")

    skipped = []
    n = copy_tree(CLONE_ROOT, TARGET_ROOT, skipped)
    print(f"  복사: {n}개 파일 (기존 파일은 보존)")
    print(f"  {install_gitignore(TARGET_ROOT / '.gitignore')}")

    for d in HARNESS_DIRS:
        p = TARGET_ROOT / d
        if not p.exists():
            p.mkdir(parents=True)
            (p / ".gitkeep").touch()
            print(f"  디렉토리 생성: {d}/")

    install_docker(assume_yes, want_docker)

    shutil.rmtree(CLONE_ROOT)
    print(f"  clone 삭제: {CLONE_ROOT.name}/")

    if "AGENTS.md" in conflicts:
        print("  ⚠ 기존 AGENTS.md 발견 — harness 버전을 AGENTS.harness.md 로 저장했습니다.")
        print("    두 파일을 수동 병합한 뒤 AGENTS.harness.md 를 삭제하세요.")
    if "CLAUDE.md" in conflicts:
        print("  ⚠ 기존 CLAUDE.md 발견 — harness 버전을 CLAUDE.harness.md 로 저장했습니다.")
        print("    기존 CLAUDE.md에 `@AGENTS.md` 줄을 추가한 뒤 CLAUDE.harness.md 를 삭제하세요.")
    others = [path for path in skipped if path not in CONFLICT_FILES]
    if others:
        print(f"  ⚠ 기존 파일이 있어 복사하지 않았습니다: {', '.join(others)}")
        print("    hook 설정이 있으면 하네스 내용을 직접 병합하세요.")
    print("  ✓ 완료. 이제 프로젝트 루트에서 `python3 .harness/setup.py`를 실행하세요.")
    print("    공유 파일이 .gitignore에 제외되어 있으면 setup.py가 알려 줍니다.\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="작업 레포 안에 클론한 harness 템플릿을 적용한다.")
    ap.add_argument("--yes", action="store_true", help="확인 프롬프트 생략")
    ap.add_argument("--with-docker", action="store_true",
                    help="Docker/devcontainer 개발 환경 스캐폴드도 함께 설치")
    ap.add_argument("--without-docker", action="store_true",
                    help="Docker 스캐폴드 설치 안 함 (프롬프트 생략)")
    args = ap.parse_args()

    if args.with_docker and args.without_docker:
        ap.error("--with-docker와 --without-docker는 동시에 줄 수 없습니다.")

    want_docker = True if args.with_docker else (False if args.without_docker else None)
    return run_install(args.yes, want_docker)


if __name__ == "__main__":
    sys.exit(main())
