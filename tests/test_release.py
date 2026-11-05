"""릴리즈 자동화(release-please) 설정을 검사한다. 템플릿 자신의 것과 PR 방식 프로젝트에 설치하는 것이 있다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "{% if main_via_pr %}.github{% endif %}"   # main_via_pr: true 프로젝트의 .github


def test_release_notes_list_merged_pull_requests():
    """병합 커밋 본문에 PR 제목이 들어가 커밋 기반 목록은 항목이 두 번씩 나온다."""
    config = json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))
    assert config["changelog-type"] == "github"


def test_version_file_matches_manifest():
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
    assert (ROOT / "version.txt").read_text(encoding="utf-8").strip() == manifest["."]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_project_config_matches_the_template_but_starts_at_0_1_0():
    project = read_json(PROJECT / "release-please-config.json")
    assert project.pop("initial-version") == "0.1.0"
    assert project == read_json(ROOT / "release-please-config.json")


def test_project_workflow_matches_the_template_but_reads_its_github_folder():
    own = (ROOT / ".github/workflows/release-please.yml").read_text(encoding="utf-8")
    for name in ("release-please-config.json", ".release-please-manifest.json"):
        own = own.replace(f": {name}\n", f": .github/{name}\n")
    assert (PROJECT / "workflows/release.yml").read_text(encoding="utf-8") == own
