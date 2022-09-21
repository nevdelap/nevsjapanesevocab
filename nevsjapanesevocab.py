#!/usr/bin/python
import re
import sys
from typing import Final, NamedTuple
from colors import color  # type: ignore
from commands import CommandStack
from localisation import _, set_locale
from operations import format_help, get_operations
from vocab import Vocab


def main() -> None:
    set_locale("ja")
    print(color(_("nevs-japanese-vocab-list"), style="bold"))

    vocab_file: Final = "vocab.csv"
    try:
        print(_("loading") + "...")
        vocab = Vocab(vocab_file)
    except IOError as err:
        print(
            _("{vocab_file}-failed-to-read-{err}").format(vocab_file=vocab_file, e=err)
        )
        sys.exit(1)

    command_stack = CommandStack()
    print(format_help())

    search: str = ""
    kanji_found: list[str] = []
    try:
        while True:
            # This is called by tests.
            (search, kanji_found) = main_stuff(
                vocab,
                command_stack,
                previous_search=search,
                previous_kanji_found=kanji_found,
            )
    except BaseException:
        print(_("saving") + "...")
        vocab.save()
        raise


# Called by tests.
def main_stuff(
    vocab: Vocab,
    command_stack: CommandStack,
    previous_search: str,
    previous_kanji_found: list[str],
) -> tuple[str, list[str]]:  # search, kanji found.
    search = "".join(
        [
            c if c.isalnum() else " "
            for c in input(_("search") + ": ")
            if c.isalnum() or c.isspace()
        ]
    ).strip()
    parts = [part for part in search.split(" ") if len(part) > 0]
    exact = False
    if len(parts) == 0:
        search = previous_search
    else:
        command = parts[0] if len(parts) > 0 else ""
        params = parts[1:] if len(parts) > 1 else []
        params = do_shortcuts(command, params, len(previous_search) > 0)
        if command == "q" and len(params) == 0:
            sys.exit()
        operations = get_operations()
        if command in operations:
            operation_descriptor = operations[command]
            params = replace_indices(
                vocab,
                previous_search,
                previous_kanji_found,
                params,
                operation_descriptor.accepts_english_params,
            )
            if operation_descriptor.are_good_params(
                params
            ) and operation_descriptor.operation_is_valid(command_stack):
                result = operation_descriptor.operation(command_stack, vocab, params)

                if result.message is not None:
                    print(result.message)
                if result.invalidate_previous_results:
                    previous_kanji_found = []
                if result.new_search is None:
                    search = previous_search
                    if not result.repeat_previous_search:
                        return search, previous_kanji_found
                else:
                    search = result.new_search
                    exact = True
            else:
                print(operation_descriptor.error_message)
                search = previous_search
        elif len(params) > 0:
            print(_("usage-h-to-show-usage"))
            return previous_search, previous_kanji_found

    if search == "":
        return "", previous_kanji_found

    kanji_found = vocab.search(search, exact)
    if len(kanji_found) > 0:
        print(_("found") + f": ({len(kanji_found)})")
        for kanji_index, kanji in enumerate(kanji_found):
            out = [
                color(f"{kanji_index + 1:4d}", fg="grey")
                + " "
                + color(vocab.get_list_name(kanji), fg="grey")
                + " "
                + kanji
            ]
            kana_list = vocab.get_kana(kanji)
            if len(kana_list) > 0:
                out.append(
                    color(
                        " ".join(
                            [
                                f'{color(str(kana_index + 1), fg="grey")} {kana}'
                                for kana_index, kana in enumerate(kana_list)
                            ]
                        ),
                        fg="grey",
                    )
                )
            if vocab.is_known(kanji):
                green_tick = color("✓", fg="green")
                out.append(green_tick)
            print("  " + " ".join(out))
    else:
        print(_("nothing-found"))
    return search, kanji_found


class Shortcut(NamedTuple):
    command: str
    actual_params: list[str]
    new_params: list[str]
    requires_previous_search: bool


Shortcuts = list[Shortcut]


def __shortcuts() -> Shortcuts:
    return [
        Shortcut("a", [], ["0"], True),
        Shortcut("l", [], ["0"], True),
    ]


# Allows replacing a given command's actual parameters with different
# parameters.
def do_shortcuts(
    command: str, params: list[str], has_previous_search: bool
) -> list[str]:
    params = params.copy()
    for shortcut in __shortcuts():
        if (
            command == shortcut.command
            and params == shortcut.actual_params
            and (not shortcut.requires_previous_search or has_previous_search)
        ):
            params = shortcut.new_params
    return params


def replace_indices(
    vocab: Vocab,
    previous_search: str,
    kanji_found: list[str],
    params: list[str],
    accepts_english_params: bool,
) -> list[str]:
    """Given a set of search results, and command
    parameters that reference kanji and kana by index in
    those results, replace the indices with the kanji and
    kana. Replace index 0 with the previous search term."""
    assert all(Vocab.valid_string(kanji) for kanji in kanji_found)
    assert all(kanji in vocab for kanji in kanji_found)
    assert all(len(p) > 0 for p in params)
    kanji = None
    if len(params) > 0:
        if not __is_index(params[0]):
            kanji = params[0]
        else:
            kanji_index = int(params[0]) - 1
            if kanji_index == -1 and len(previous_search) > 0:
                params[0] = previous_search
            elif 0 <= kanji_index < len(kanji_found):
                kanji = kanji_found[kanji_index]
                params[0] = kanji
    if kanji is not None and len(params) > 1 and __is_index(params[1]):
        kana = vocab.get_kana(kanji)
        kana_index = int(params[1]) - 1
        if 0 <= kana_index < len(kana):
            params[1] = kana[kana_index]
    params = [
        param
        for param in params
        if accepts_english_params and not __is_index(param) or is_kanji_or_kana(param)
    ]
    return params


def __is_index(s: str) -> bool:
    # Because isnumeric doesn't know about negative numbers.
    return re.match("^[-+]?[0-9]+$", s) is not None


def is_kanji_or_kana(s: str) -> bool:
    return (
        re.match("^[\u3005\u3007\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FBF]+$", s)
        is not None
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
