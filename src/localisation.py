from gettext import NullTranslations, translation
from typing import Callable, Dict


GetText = Callable[[str], str]

# Default passthrough for tests.
__: GetText = lambda s: s


def _(s: str) -> str:
    """_() is provided rather than using gettext's install() so that mypy doesn't complain that the name '_' is not defined."""
    return __(s)


__translations: Dict[
    str,  # locale.
    NullTranslations
] = {}


def set_locale(locale: str) -> None:
    if locale not in __translations:
        __translations[locale] = translation(
            'messages', localedir='locales', languages=[locale])
    global __
    __ = __translations[locale].gettext
