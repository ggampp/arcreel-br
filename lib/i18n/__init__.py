from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, Request

from .en import assets as en_assets
from .en import emails as en_emails
from .en import errors as en_errors
from .en import providers as en_providers
from .en import system as en_system
from .en import templates as en_templates
from .pt import assets as pt_assets
from .pt import emails as pt_emails
from .pt import errors as pt_errors
from .pt import providers as pt_providers
from .pt import system as pt_system
from .pt import templates as pt_templates

logger = logging.getLogger(__name__)

# Default locale: Brazilian Portuguese
DEFAULT_LOCALE = "pt"
SUPPORTED_LOCALES = ["pt", "en"]

# Mapping from locale code to human-readable language name
LOCALE_LANGUAGE_MAP: dict[str, str] = {
    "pt": "Português (Brasil)",
    "en": "English",
}

# Merged message dictionary
MESSAGES: dict[str, dict[str, str]] = {
    "pt": {
        **pt_errors.MESSAGES,
        **pt_system.MESSAGES,
        **pt_emails.MESSAGES,
        **pt_providers.MESSAGES,
        **pt_templates.MESSAGES,
        **pt_assets.MESSAGES,
    },
    "en": {
        **en_errors.MESSAGES,
        **en_system.MESSAGES,
        **en_emails.MESSAGES,
        **en_providers.MESSAGES,
        **en_templates.MESSAGES,
        **en_assets.MESSAGES,
    },
}


def get_locale(request: Request) -> str:
    """Get locale from Accept-Language header.

    Supports BCP47 tags such as ``pt-BR``, ``en-US`` by matching the primary
    subtag against :data:`SUPPORTED_LOCALES` (``pt``, ``en``).
    """
    accept_lang = request.headers.get("accept-language", "")
    if not accept_lang:
        return DEFAULT_LOCALE

    # e.g. "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    for lang_range in accept_lang.split(","):
        raw = lang_range.split(";")[0].strip().lower().replace("_", "-")
        if not raw:
            continue
        # Exact match first (if we ever add regional codes)
        if raw in SUPPORTED_LOCALES:
            return raw
        primary = raw.split("-")[0]
        if primary in SUPPORTED_LOCALES:
            return primary

    return DEFAULT_LOCALE


def get_translator(request: Request) -> Callable[..., str]:
    """Dependency to get a translator function for the current request."""
    locale = get_locale(request)

    def translate(key: str, **kwargs: Any) -> str:
        return _(key, locale=locale, **kwargs)

    return translate


Translator = Annotated[Callable[..., str], Depends(get_translator)]


def _(key: str, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    """Translate a message key to the given locale."""
    msg_map = MESSAGES.get(locale, MESSAGES[DEFAULT_LOCALE])
    msg = msg_map.get(key, MESSAGES[DEFAULT_LOCALE].get(key, key))
    try:
        return msg.format(**kwargs)
    except Exception:
        return msg
