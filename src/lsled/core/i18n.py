"""Load message catalogs and determine the language from the system environment."""
import json
import os
import subprocess
import sys
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locales"
FALLBACK = "en"

_messages: dict[str, str] | None = None


def available_languages() -> list[str]:
    return sorted(path.stem for path in LOCALE_DIR.glob("*.json"))


def match_language(tag: str) -> str | None:
    """Map a locale such as de_DE.UTF-8, zh-Hans-CN or nn_NO to an available catalog."""
    parts = tag.split(".")[0].split("@")[0].replace("_", "-").lower().split("-")
    language = parts[0]
    if language == "zh":
        # Only Simplified Chinese exists; traditional variants fall back to English
        traditional = {"hant", "tw", "hk", "mo"} & set(parts[1:])
        return None if traditional else "zh-Hans"
    if language in ("no", "nn"):
        language = "nb"
    return language if language in available_languages() else None


def system_language() -> str:
    # Same order as gettext; LANGUAGE may be a list such as "de:en"
    candidates = os.environ.get("LANGUAGE", "").split(":")
    candidates += [os.environ.get(name, "") for name in ("LC_ALL", "LC_MESSAGES", "LANG")]
    if not any(candidates) and sys.platform == "darwin":
        # Without any variables set, use the region from the macOS settings
        result = subprocess.run(["defaults", "read", "-g", "AppleLocale"], capture_output=True, text=True)
        candidates.append(result.stdout.strip())
    for tag in candidates:
        if tag and tag not in ("C", "POSIX") and (language := match_language(tag)):
            return language
    return FALLBACK


def load_messages(language: str) -> dict[str, str]:
    """Catalog for the language, missing keys filled in from English."""
    messages = json.loads((LOCALE_DIR / f"{FALLBACK}.json").read_text(encoding="utf-8"))
    if language != FALLBACK:
        messages.update(json.loads((LOCALE_DIR / f"{language}.json").read_text(encoding="utf-8")))
    return messages


class LocalizedError(ValueError):
    """Error whose message is looked up per language when it is shown."""

    def __init__(self, key: str, **values):
        super().__init__(key)
        self.key = key
        self.values = values

    def __str__(self) -> str:
        return t(self.key, **self.values)

    def translate(self, messages: dict[str, str], key: str | None = None) -> str:
        return messages[key or self.key].format(**self.values)


def t(key: str, **values) -> str:
    global _messages
    if _messages is None:
        _messages = load_messages(system_language())
    return _messages[key].format(**values)
