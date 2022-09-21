import re


def strip_ansi_terminal_escapes(s: str) -> str:
    return re.sub("\x1b\\[[\\d;]+m", "", s)
