"""Verify that i18n translation dictionaries are consistent across locales."""

from lib.i18n import MESSAGES, SUPPORTED_LOCALES
from lib.i18n.en import emails as en_emails
from lib.i18n.en import errors as en_errors
from lib.i18n.en import system as en_system
from lib.i18n.en import templates as en_templates
from lib.i18n.pt import emails as pt_emails
from lib.i18n.pt import errors as pt_errors
from lib.i18n.pt import system as pt_system
from lib.i18n.pt import templates as pt_templates
from lib.style_templates import STYLE_TEMPLATES


def test_supported_locales_are_pt_and_en_only():
    """UI/backend locales are Brazilian Portuguese + English only."""
    assert set(SUPPORTED_LOCALES) == {"pt", "en"}
    assert set(MESSAGES.keys()) == {"pt", "en"}


def test_all_locales_have_same_keys():
    """Every locale must define the exact same set of merged keys."""
    key_sets = {locale: set(msgs.keys()) for locale, msgs in MESSAGES.items()}
    locales = list(key_sets.keys())
    for i in range(1, len(locales)):
        missing = key_sets[locales[0]] - key_sets[locales[i]]
        extra = key_sets[locales[i]] - key_sets[locales[0]]
        assert not missing, f"{locales[i]} is missing keys present in {locales[0]}: {missing}"
        assert not extra, f"{locales[i]} has extra keys not in {locales[0]}: {extra}"


def test_errors_module_keys_match():
    en_keys = set(en_errors.MESSAGES.keys())
    pt_keys = set(pt_errors.MESSAGES.keys())
    assert en_keys == pt_keys, (
        f"en-pt errors key mismatch: missing_in_pt={en_keys - pt_keys}, missing_in_en={pt_keys - en_keys}"
    )


def test_system_module_keys_match():
    en_keys = set(en_system.MESSAGES.keys())
    pt_keys = set(pt_system.MESSAGES.keys())
    assert en_keys == pt_keys, (
        f"en-pt system key mismatch: missing_in_pt={en_keys - pt_keys}, missing_in_en={pt_keys - en_keys}"
    )


def test_emails_module_keys_match():
    en_keys = set(en_emails.MESSAGES.keys())
    pt_keys = set(pt_emails.MESSAGES.keys())
    assert en_keys == pt_keys, (
        f"en-pt emails key mismatch: missing_in_pt={en_keys - pt_keys}, missing_in_en={pt_keys - en_keys}"
    )


def test_templates_module_keys_match():
    en_keys = set(en_templates.MESSAGES.keys())
    pt_keys = set(pt_templates.MESSAGES.keys())
    assert en_keys == pt_keys, (
        f"en-pt templates key mismatch: missing_in_pt={en_keys - pt_keys}, missing_in_en={pt_keys - en_keys}"
    )


def test_templates_cover_all_style_template_ids():
    """STYLE_TEMPLATES 的每个 id 都必须在 pt/en templates 里有 name 与 tagline key。"""
    required_name_keys = {f"template_name_{tid}" for tid in STYLE_TEMPLATES}
    required_tagline_keys = {f"template_tagline_{tid}" for tid in STYLE_TEMPLATES}
    for module_name, msgs in (
        ("pt", pt_templates.MESSAGES),
        ("en", en_templates.MESSAGES),
    ):
        missing_names = required_name_keys - set(msgs.keys())
        missing_taglines = required_tagline_keys - set(msgs.keys())
        assert not missing_names, f"{module_name} templates missing name keys: {missing_names}"
        assert not missing_taglines, f"{module_name} templates missing tagline keys: {missing_taglines}"


def test_supported_locales_all_present():
    """SUPPORTED_LOCALES must match the locales in MESSAGES."""
    assert set(SUPPORTED_LOCALES) == set(MESSAGES.keys())


def test_format_placeholders_consistent():
    """All locales must use the same format placeholders for each key."""
    import re

    placeholder_re = re.compile(r"\{(\w+)\}")
    base_locale = SUPPORTED_LOCALES[0]

    for key in MESSAGES[base_locale]:
        base_placeholders = set(placeholder_re.findall(MESSAGES[base_locale][key]))
        for locale in SUPPORTED_LOCALES[1:]:
            if key not in MESSAGES[locale]:
                continue
            locale_placeholders = set(placeholder_re.findall(MESSAGES[locale][key]))
            assert base_placeholders == locale_placeholders, (
                f"Key '{key}': {base_locale} uses {base_placeholders} but {locale} uses {locale_placeholders}"
            )
