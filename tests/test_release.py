"""템플릿 레포의 릴리즈 자동화(release-please) 설정을 검사한다."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def sections():
    config = json.loads((ROOT / "release-please-config.json").read_text(encoding="utf-8"))
    return {section["type"]: section for section in config["packages"]["."]["changelog-sections"]}


@pytest.mark.parametrize("kind", ["feat", "fix", "hotfix", "docs", "refactor"])
def test_harness_changes_reach_a_release(kind):
    """규칙 문서(docs)도 프로젝트 동작을 바꾸므로 릴리즈 대상이다."""
    assert not sections()[kind].get("hidden", False)


def test_version_file_matches_manifest():
    manifest = json.loads((ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))
    assert (ROOT / "version.txt").read_text(encoding="utf-8").strip() == manifest["."]
