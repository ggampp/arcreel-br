"""BrandProfile / ad_timeline / continuation / consistency 单元测试。"""

from __future__ import annotations

from pathlib import Path

from lib.ad_consistency import critique_ad_shot
from lib.ad_continuation import ad_continuation_enabled, last_frame_relpath, resolve_previous_item
from lib.ad_timeline import ad_video_takes, normalize_ad_timeline, validate_ad_timeline
from lib.brand_profile import (
    derive_style_prefix,
    empty_brand_profile,
    merge_brand_profile,
    normalize_brand_profile,
    validate_brand_profile,
)
from lib.product_isolation import isolated_ref_filename, rembg_available
from lib.project_manager import ProjectManager


def test_empty_and_normalize():
    empty = empty_brand_profile()
    assert empty["style_prefix"] == ""
    assert empty["brand_colors"] == []
    norm = normalize_brand_profile({"visual_description": "红瓶", "brand_colors": ["#f00", 1]})
    assert norm["visual_description"] == "红瓶"
    assert norm["brand_colors"] == ["#f00"]


def test_validate_and_merge():
    assert validate_brand_profile("x") == ["brand_profile 必须是对象"]
    assert validate_brand_profile({"tone_of_voice": 1})
    merged = merge_brand_profile({}, {"style_prefix": "glossy", "style_keywords": ["clean"]})
    assert merged["style_prefix"] == "glossy"
    assert merged["style_keywords"] == ["clean"]


def test_derive_style_prefix_explicit_and_derived():
    assert derive_style_prefix({"style_prefix": "FIXED"}) == "FIXED"
    derived = derive_style_prefix(
        {
            "visual_description": "银色铝罐",
            "style_keywords": ["冷感"],
            "brand_colors": ["#abc"],
        }
    )
    assert "银色铝罐" in derived
    assert "冷感" in derived


def test_ad_project_creates_brand_and_timeline_defaults(tmp_path: Path):
    pm = ProjectManager(tmp_path / "projects")
    pm.create_project("ad1", content_mode="ad")
    project = pm.create_project_metadata("ad1", "Demo", "Realistic", "ad")
    assert project["brand_profile"]["style_prefix"] == ""
    assert project["ad_timeline"]["text_overlays"] == []
    assert project["ad_continuation"] is True
    assert project["ad_video_takes"] == 1


def test_ad_timeline_validate_and_normalize():
    errs = validate_ad_timeline({"text_overlays": [{"text": "hi", "start": 0, "end": 1, "position": "side"}]})
    assert errs
    norm = normalize_ad_timeline(
        {
            "text_overlays": [{"text": "限时", "start": 0, "end": 2, "position": "bottom"}],
            "music_track": "music/a.mp3",
        }
    )
    assert norm["text_overlays"][0]["text"] == "限时"
    assert norm["music_track"] == "music/a.mp3"


def test_ad_video_takes_clamp():
    assert ad_video_takes({"content_mode": "ad"}, 5) == 3
    assert ad_video_takes({"content_mode": "ad", "ad_video_takes": 1}) == 1
    assert ad_video_takes({"content_mode": "narration"}) == 1


def test_continuation_helpers():
    assert ad_continuation_enabled({"content_mode": "ad"}) is True
    assert ad_continuation_enabled({"content_mode": "ad", "ad_continuation": False}) is False
    assert ad_continuation_enabled({"content_mode": "drama"}) is False
    items = [{"shot_id": "E1S01"}, {"shot_id": "E1S02"}]
    assert resolve_previous_item(items, "shot_id", "E1S02")["shot_id"] == "E1S01"
    assert resolve_previous_item(items, "shot_id", "E1S01") is None
    assert last_frame_relpath("E1S01").endswith("E1S01_last.png")


def test_critique_atmosphere_and_missing_product(tmp_path: Path):
    project = {"products": {}}
    atm = critique_ad_shot(
        project=project,
        project_path=tmp_path,
        shot={"shot_id": "E1S01", "products_in_shot": []},
    )
    assert atm.passed and not atm.recommend_regen

    miss = critique_ad_shot(
        project=project,
        project_path=tmp_path,
        shot={"shot_id": "E1S02", "products_in_shot": ["Ghost"]},
    )
    assert not miss.passed and miss.recommend_regen


def test_isolated_filename_and_rembg_probe():
    assert isolated_ref_filename("foo_1.jpg") == "foo_1_isolated.png"
    # rembg 可选；只断言 API 可调用
    assert isinstance(rembg_available(), bool)


def test_data_validator_rejects_brand_on_non_ad(tmp_path: Path):
    from lib.data_validator import DataValidator

    pm = ProjectManager(tmp_path / "projects")
    pm.create_project("n1", content_mode="narration")
    project = pm.create_project_metadata("n1", "N", "Anime", "narration")
    project["brand_profile"] = empty_brand_profile()
    result = DataValidator().validate_project_payload(project)
    assert any("brand_profile" in e for e in result.errors)
