from gettext import NullTranslations
from gettext import translation
from typing import Callable
from typing import Optional

GetText = Callable[[str], str]

# Default passthrough for tests.
__no_locale: GetText = lambda s: s
__: GetText = __no_locale


def _(s: str) -> str:
    """_() is provided rather than using gettext's install()
    so that mypy doesn't complain that the name '_' is not
    defined."""
    return __(s)


# pylint: disable=invalid-name
__locale = None

__translations: dict[str, NullTranslations] = {}  # locale.


def get_locale() -> Optional[str]:
    return __locale


def set_locale(locale: str) -> None:
    # pylint: disable=global-statement
    global __locale
    __locale = locale
    if __locale not in __translations:
        __translations[__locale] = translation(
            "messages", localedir="locales", languages=[__locale]
        )
    # pylint: disable=global-statement
    global __
    __ = __translations[__locale].gettext


def unset_locale() -> None:
    __locale = None
    __ = __no_locale
