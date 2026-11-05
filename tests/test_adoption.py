"""실제 순서대로 도입한다: 이력과 충돌 규칙이 있는 프로젝트 → copier 설치 → setup → 커밋 → 새 clone."""
import pytest

from test_copier import git, install, make_template
from test_setup import run_setup, shared_files

GOOD = "chore(harness): add harness\n\n- add shared rules and hooks"
CONFLICTING = ".claude/\ndocs/\nCLAUDE.md\n"


@pytest.fixture
def project(tmp_path):
    path = tmp_path / "project"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    (path / "app.py").write_text("print('app')\n")
    (path / ".gitignore").write_text(CONFLICTING)
    git(path, "add", ".")
    assert git(path, "commit", "-qm", "init").returncode == 0
    git(path, "switch", "-q", "-c", "chore/add-harness")
    return path


def test_conflicting_gitignore_is_reported_and_fix_reaches_new_clone(project, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    template = make_template(tmp_path / "template")
    assert install(template, project).returncode == 0

    blocked = run_setup(project, bin_dir)
    assert blocked.returncode == 1
    assert ".claude/settings.json" in blocked.stdout and "docs/ADR.md" in blocked.stdout

    gitignore = project / ".gitignore"
    gitignore.write_text(gitignore.read_text().replace(CONFLICTING, ""))
    assert run_setup(project, bin_dir).returncode == 0

    git(project, "add", ".")
    assert git(project, "commit", "-qm", GOOD).returncode == 0

    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", "-b", "chore/add-harness", str(project), str(clone))
    assert [rel for rel in shared_files() if not (clone / rel).is_file()] == []
    assert (clone / ".copier-answers.yml").is_file()
    assert run_setup(clone, bin_dir).returncode == 0
    assert git(clone, "status", "--porcelain").stdout == ""

    git(clone, "switch", "-q", "-c", "wrong-name")
    (clone / "b.txt").write_text("b\n")
    git(clone, "add", "b.txt")
    assert git(clone, "commit", "-qm", GOOD).returncode != 0
