"""가짜 에이전트 CLI를 둔 임시 저장소에서 setup.py를 실제로 실행해 검사한다."""
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / ".harness/setup.py"
GIT_DIR = str(Path(shutil.which("git")).parent)
# XDG_CONFIG_HOME도 막는다. 그렇지 않으면 사용자 전역 제외 파일(~/.config/git/ignore)이 결과를 바꾼다.
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
       "XDG_CONFIG_HOME": os.devnull}

INSTALL = {
    "claude": "plugin install superpowers --marketplace anthropics/claude-plugins-official",
    "codex": "plugin add superpowers@openai-curated-remote",
    "agy": "plugin install https://github.com/obra/superpowers",
}
NOT_INSTALLED = "superpowers@x  not installed"
INSTALLED = "superpowers@x  installed, enabled"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=ENV)


def hooks_path(repo):
    return git(repo, "config", "core.hooksPath").stdout.strip()


IGNORED = [
    "docs/private/x", "references/x", "scratch/x", "continuation_plan.md", ".env",
    ".claude/settings.local.json",
]
RESEARCH_IGNORED = [
    "experiments/feat-x/log.md", "a.pth", "a.pt", "a.ckpt", "a.safetensors", "d.zarr/x", "symlinked.zarr",
    "a.hdf5", "a.h5", "wandb/x", "outputs/x",
]
RESEARCH_FILES = ("docs/RESEARCH.md", ".harness/LOG_TEMPLATE.md")
TRACKED = [
    ".claude/settings.json", ".claude/skills/harness/SKILL.md", ".copier-answers.yml", "docs/ADR.md",
]
BEGIN = "# >>> harness gitignore (managed) >>>"
END = "# <<< harness gitignore (managed) <<<"


def load_setup():
    spec = importlib.util.spec_from_file_location("harness_setup", SETUP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shared_files():
    return load_setup().SHARED_FILES


def place_shared_files(path):
    for rel in shared_files():
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, path / rel)


@pytest.fixture
def bin_dir(tmp_path):
    path = tmp_path / "bin"
    path.mkdir()
    return path


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    place_shared_files(path)
    git(path, "init", "-q", "-b", "main")
    return path


def answer(path, research, main_via_pr=True):
    (path / ".copier-answers.yml").write_text(
        f"research: {str(research).lower()}\nmain_via_pr: {str(main_via_pr).lower()}\n")


@pytest.fixture
def research_repo(repo):
    """research=true로 설치한 프로젝트. setup.py는 연구 파일이 있는지만 본다."""
    answer(repo, research=True)
    for rel in RESEARCH_FILES:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("x\n")
    return repo


def fake_agent(bin_dir, name, listed=NOT_INSTALLED, install_exit=0):
    """호출 인자를 로그에 남긴다. `plugin list`는 listed를 출력한다."""
    path = bin_dir / name
    path.write_text(
        "#!/bin/sh\n"
        f'echo "$*" >> "{bin_dir}/{name}.log"\n'
        f'if [ "$1 $2" = "plugin list" ]; then echo "{listed}"; exit 0; fi\n'
        f"exit {install_exit}\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def calls(bin_dir, name):
    log = bin_dir / f"{name}.log"
    return log.read_text().splitlines() if log.exists() else []


def run_setup(repo, bin_dir):
    env = {**ENV, "PATH": f"{bin_dir}{os.pathsep}{GIT_DIR}"}
    return subprocess.run([sys.executable, ".harness/setup.py"], cwd=repo,
                          capture_output=True, text=True, env=env)


def test_connects_hooks_without_agents(repo, bin_dir):
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"


def test_keeps_other_hooks_path(repo, bin_dir):
    git(repo, "config", "core.hooksPath", ".husky")
    result = run_setup(repo, bin_dir)
    assert hooks_path(repo) == ".husky"
    assert ".husky" in result.stdout and result.returncode == 1


def test_keeps_user_hook(repo, bin_dir):
    (repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\n")
    result = run_setup(repo, bin_dir)
    assert hooks_path(repo) == ""
    assert "pre-commit" in result.stdout and result.returncode == 1


def test_sample_hooks_do_not_count(repo, bin_dir):
    (repo / ".git/hooks/pre-commit.sample").write_text("#!/bin/sh\n")
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"


@pytest.mark.parametrize("rel", IGNORED)
def test_ignores_local_and_large_files(repo, bin_dir, rel):
    run_setup(repo, bin_dir)
    assert git(repo, "check-ignore", "-q", rel).returncode == 0


@pytest.mark.parametrize("rel", RESEARCH_IGNORED)
def test_research_ignores_experiments_and_large_files(research_repo, bin_dir, rel):
    assert run_setup(research_repo, bin_dir).returncode == 0
    assert git(research_repo, "check-ignore", "-q", rel).returncode == 0


@pytest.mark.parametrize("rel", ["experiments/feat-x/log.md", "a.pth", "outputs/x"])
def test_without_research_experiments_and_large_files_are_not_ignored(repo, bin_dir, rel):
    run_setup(repo, bin_dir)
    assert git(repo, "check-ignore", "-q", rel).returncode == 1


def test_block_follows_research_answer(research_repo, bin_dir):
    run_setup(research_repo, bin_dir)
    answer(research_repo, research=False)
    run_setup(research_repo, bin_dir)
    assert git(research_repo, "check-ignore", "-q", "a.pth").returncode == 1


@pytest.mark.parametrize("rel", RESEARCH_FILES)
def test_research_reports_missing_research_file(research_repo, bin_dir, rel):
    (research_repo / rel).unlink()
    result = run_setup(research_repo, bin_dir)
    assert rel in result.stdout and result.returncode == 1


def test_options_default_without_answers(tmp_path):
    assert load_setup().options(tmp_path) == {"research": False, "main_via_pr": True}


def test_options_read_answers(tmp_path):
    answer(tmp_path, research=True, main_via_pr=False)
    assert load_setup().options(tmp_path) == {"research": True, "main_via_pr": False}


@pytest.mark.parametrize("rel", TRACKED)
def test_keeps_shared_files_tracked(repo, bin_dir, rel):
    run_setup(repo, bin_dir)
    assert git(repo, "check-ignore", "-q", rel).returncode == 1


def test_appends_block_after_existing_rules(repo, bin_dir):
    (repo / ".gitignore").write_text("data/")
    run_setup(repo, bin_dir)
    text = (repo / ".gitignore").read_text()
    assert text.startswith("data/\n\n" + BEGIN) and text.endswith(END + "\n")


def test_replaces_outdated_managed_block(repo, bin_dir):
    (repo / ".gitignore").write_text(f"before\n\n{BEGIN}\n/docs/\n{END}\n\nafter\n")
    run_setup(repo, bin_dir)
    text = (repo / ".gitignore").read_text()
    assert "/docs/\n" not in text and "/scratch/" in text and text.count(BEGIN) == 1
    assert text.startswith("before\n\n") and text.endswith("\n\nafter\n")


def test_second_run_leaves_gitignore_unchanged(repo, bin_dir):
    run_setup(repo, bin_dir)
    before = (repo / ".gitignore").read_text()
    result = run_setup(repo, bin_dir)
    assert (repo / ".gitignore").read_text() == before and ".gitignore" not in result.stdout


def test_template_gitignore_has_current_block():
    """템플릿 레포에는 답 파일이 없어 research=false 블록을 쓴다."""
    setup = load_setup()
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert setup.gitignore_with_block(text, setup.gitignore_block(research=False)) == text


def test_directories_do_not_count_as_hooks(repo, bin_dir):
    (repo / ".git/hooks/helpers").mkdir()
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"


def test_agent_that_cannot_start_is_reported(repo, bin_dir):
    agent = bin_dir / "codex"
    agent.write_text("#!/nonexistent/interpreter\n")
    agent.chmod(0o755)
    result = run_setup(repo, bin_dir)
    assert INSTALL["codex"] in result.stdout and result.returncode == 1


def test_reports_failed_hook_connection(repo, bin_dir):
    (repo / ".git/config.lock").touch()
    result = run_setup(repo, bin_dir)
    assert "연결했습니다" not in result.stdout and result.returncode == 1


def test_reports_harness_below_repo_root(tmp_path, bin_dir):
    outer = tmp_path / "outer"
    project = outer / "sub"
    place_shared_files(project)
    git(outer, "init", "-q", "-b", "main")
    result = run_setup(project, bin_dir)
    assert hooks_path(project) == ""
    assert "루트" in result.stdout and result.returncode == 1


def test_reports_shared_files_excluded_by_gitignore(repo, bin_dir):
    (repo / ".gitignore").write_text(".claude/\nCLAUDE.md\ndocs/\n")
    result = run_setup(repo, bin_dir)
    for rel in (".claude/settings.json", ".claude/skills/harness/SKILL.md", "CLAUDE.md", "docs/ADR.md"):
        assert rel in result.stdout
    assert result.returncode == 1


def test_accepts_tracked_file_matching_gitignore(repo, bin_dir):
    (repo / ".gitignore").write_text("CLAUDE.md\n")
    git(repo, "add", "-f", "CLAUDE.md")
    assert run_setup(repo, bin_dir).returncode == 0


def test_reports_missing_shared_file(repo, bin_dir):
    (repo / ".codex/hooks.json").unlink()
    result = run_setup(repo, bin_dir)
    assert ".codex/hooks.json" in result.stdout and result.returncode == 1


def test_reports_hook_without_execute_permission(repo, bin_dir):
    (repo / ".githooks/pre-push").chmod(0o644)
    result = run_setup(repo, bin_dir)
    assert ".githooks/pre-push" in result.stdout and result.returncode == 1


def test_reports_claude_md_without_import(repo, bin_dir):
    (repo / "CLAUDE.md").write_text("mine\n")
    result = run_setup(repo, bin_dir)
    assert "@AGENTS.md" in result.stdout and result.returncode == 1


def test_outside_git_repo_explains_git_init(tmp_path, bin_dir):
    path = tmp_path / "plain"
    (path / ".harness").mkdir(parents=True)
    shutil.copy2(SETUP, path / ".harness/setup.py")
    result = run_setup(path, bin_dir)
    assert "git init" in result.stdout and result.returncode == 1


def test_installs_superpowers_for_each_agent(repo, bin_dir):
    for name in INSTALL:
        fake_agent(bin_dir, name)
    assert run_setup(repo, bin_dir).returncode == 0
    for name, command in INSTALL.items():
        assert calls(bin_dir, name) == ["plugin list", command]


def test_not_installed_row_still_installs(repo, bin_dir):
    fake_agent(bin_dir, "codex", listed=NOT_INSTALLED)
    run_setup(repo, bin_dir)
    assert INSTALL["codex"] in calls(bin_dir, "codex")


def test_installed_plugin_is_skipped(repo, bin_dir):
    fake_agent(bin_dir, "codex", listed=INSTALLED)
    assert run_setup(repo, bin_dir).returncode == 0
    assert calls(bin_dir, "codex") == ["plugin list"]


def test_rerun_on_configured_clone_changes_nothing(repo, bin_dir):
    git(repo, "config", "core.hooksPath", ".githooks")
    fake_agent(bin_dir, "claude", listed=INSTALLED)
    assert run_setup(repo, bin_dir).returncode == 0
    assert hooks_path(repo) == ".githooks"
    assert calls(bin_dir, "claude") == ["plugin list"]


def test_failed_install_continues_and_reports(repo, bin_dir):
    fake_agent(bin_dir, "codex", install_exit=1)
    fake_agent(bin_dir, "agy")
    result = run_setup(repo, bin_dir)
    assert INSTALL["agy"] in calls(bin_dir, "agy")
    assert INSTALL["codex"] in result.stdout and result.returncode == 1


def test_prints_manual_trust_steps(repo, bin_dir):
    fake_agent(bin_dir, "claude", listed=INSTALLED)
    fake_agent(bin_dir, "codex", listed=INSTALLED)
    out = run_setup(repo, bin_dir).stdout
    assert "폴더 신뢰" in out and "/hooks" in out
    assert "승인 전에는" in out
