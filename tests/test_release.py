"""템플릿 레포의 릴리즈 자동화(release-please) 설정을 검사한다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_release_notes_list_merged_pull_requests():
    """병합 커밋 본문에 PR 제목이 들어가 커밋 기반 목록은 항목이 두 번씩 나온다."""
    config = json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))
    assert config["changelog-type"] == "github"


def test_version_file_matches_manifest():
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
    assert (ROOT / "version.txt").read_text(encoding="utf-8").strip() == manifest["."]
