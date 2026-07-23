"""assets namespace 注册到 MESSAGES。"""

from __future__ import annotations

from lib.i18n import MESSAGES, _


def test_asset_not_found_key_present_both_locales():
    pt = _("asset_not_found", locale="pt", name="X")
    assert "X" in pt and ("ativo" in pt.lower() or "não existe" in pt.lower())
    en = _("asset_not_found", locale="en", name="X")
    assert "X" in en and "Asset" in en


def test_all_asset_keys_registered_in_both_locales():
    expected = {
        "asset_not_found",
        "asset_already_exists",
        "asset_invalid_type",
        "asset_upload_too_large",
        "asset_unsupported_format",
        "asset_source_resource_not_found",
        "asset_target_project_not_found",
        "asset_load_project_failed",
        "asset_invalid_conflict_policy",
        "asset_invalid_name",
    }
    for key in expected:
        assert key in MESSAGES["pt"], f"missing pt key: {key}"
        assert key in MESSAGES["en"], f"missing en key: {key}"
