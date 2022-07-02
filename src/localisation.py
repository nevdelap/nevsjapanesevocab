from gettext import NullTranslations, translation
from typing import Callable, Dict, Optional


GetText = Callable[[str], str]

# Default passthrough for tests.
__no_locale: GetText = lambda s: s
__: GetText = __no_locale


def _(s: str) -> str:
    """_() is provided rather than using gettext's install()
    so that mypy doesn't complain that the name '_' is not
    defined."""
    return __(s)


__locale = None

__translations: Dict[
    str,  # locale.
    NullTranslations
] = {}


def get_locale() -> Optional[str]:
    return __locale


def set_locale(locale: str) -> None:
    global __locale
    __locale = locale
    if __locale not in __translations:
        __translations[__locale] = translation(
            'messages', localedir='locales', languages=[__locale])
    global __
    __ = __translations[__locale].gettext


def unset_locale() -> None:
    __locale = None
    __ = __no_locale
