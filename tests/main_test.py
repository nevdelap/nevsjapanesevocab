import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO

import pytest
from test_helpers import strip_ansi_terminal_escapes

from commands import CommandStack
from localisation import _
from localisation import set_locale
from localisation import unset_locale
from nevsjapanesevocab import is_kanji_or_kana
from nevsjapanesevocab import main_stuff
from nevsjapanesevocab import replace_indices
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    vocab = Vocab("tests/test_data/vocab_good.csv")
    vocab.add("新しい")
    vocab.add("新しい二")
    vocab.add("新しい三")
    vocab.add_kana("新しい二", "かなに")
    vocab.add_kana("新しい二", "かなさん")
    return vocab


@pytest.mark.parametrize(
    "search, params, expected_result",
    [
        ("新しい", ["-50"], []),
        ("新しい", ["-1"], []),
        ("新しい", ["0"], ["あああああ"]),
        ("新しい", ["1"], ["新しい"]),
        ("新しい", ["2"], ["新しい二"]),
        ("新しい", ["3"], ["新しい三"]),
        ("新しい", ["4"], []),
        ("新しい", ["999"], []),
        ("新しい", ["1", "1"], ["新しい", "あたらしい"]),
        ("新しい", ["新しい", "1"], ["新しい", "あたらしい"]),
        ("新しい", ["2", "-50"], ["新しい二"]),
        ("新しい", ["2", "-1"], ["新しい二"]),
        ("新しい", ["2", "0"], ["新しい二"]),
        ("新しい", ["2", "1"], ["新しい二", "あたらしいに"]),
        ("新しい", ["2", "2"], ["新しい二", "かなに"]),
        ("新しい", ["2", "3"], ["新しい二", "かなさん"]),
        ("新しい", ["2", "4"], ["新しい二"]),
        ("新しい", ["2", "999"], ["新しい二"]),
        ("新しい", ["新しい二", "-50"], ["新しい二"]),
        ("新しい", ["新しい二", "-1"], ["新しい二"]),
        ("新しい", ["新しい二", "0"], ["新しい二"]),
        ("新しい", ["新しい二", "1"], ["新しい二", "あたらしいに"]),
        ("新しい", ["新しい二", "2"], ["新しい二", "かなに"]),
        ("新しい", ["新しい二", "3"], ["新しい二", "かなさん"]),
        ("新しい", ["新しい二", "4"], ["新しい二"]),
        ("新しい", ["新しい二", "999"], ["新しい二"]),
    ],
)
def test_replace_indices(
    vocab: Vocab, search: str, params: list[str], expected_result: list[str]
) -> None:
    found_kanji = vocab.search(search)
    assert (
        replace_indices(vocab, "あああああ", found_kanji, params, False) == expected_result
    )


# This has examples of all translations to ensure that the
# translations themselves are syntactically correct in
# regards to interpolation. E.g. {new_kanji}, not
# {new-kanji}.


@dataclass
class IO:
    test_input: str
    expected_output_regex: str


def __io_general() -> list[IO]:
    return [
        IO("\n", _("search")),
        IO("l", f'{_("usage")}: l {_("kanji")}|{_("kana")}'),
        # Bad command.
        IO("w 漢字 かな", _("usage-h-to-show-usage")),
        # Bad usage.
        IO("t", f'{_("usage")}: t {_("kanji")}'),
        # Attempt add previous search when there is not previous search.
        IO("a 0", f'{_("usage")}: a {_("kanji")}'),
        # Search found and not found.
        IO("研究", f'{_("found")}: \\(1\\)\n     1 0100 研究 1 けんきゅう'),
        IO("", f'{_("found")}: \\(1\\)\n     1 0100 研究 1 けんきゅう'),
        IO("asdasd", _("nothing-found")),
        # Each command's usage when used with incorrect
        # parameters or at the wrong time.
        IO("l", _("nothing-found")),
        IO("a", f'{_("usage")}: a {_("kanji")}'),
        IO("d", f'{_("usage")}: d {_("kanji")}'),
        IO("ak", f'{_("usage")}: a {_("kanji")}{_("space")}{_("kana")}\n'),
        IO("ak new", f'{_("usage")}: a {_("kanji")}{_("space")}{_("kana")}'),
        IO("dk", f'{_("usage")}: d {_("kanji")}{_("space")}{_("kana")}'),
        IO("dk new", f'{_("usage")}: d {_("kanji")}{_("space")}{_("kana")}'),
        IO("u", _("there-is-nothing-to-undo")),
        IO("r", _("there-is-nothing-to-redo")),
        # Toggle status.
        IO("t 研究", f'{_("found")}: \\(1\\)\n     1 0100 研究 1 けんきゅう ' + "✓"),
        IO(
            "u",
            _("toggled-the-{known_status}-of-{kanji}").format(
                kanji="研究", known_status=_("unknown")
            ),
        ),
        IO(
            "r",
            _("toggled-the-{known_status}-of-{kanji}").format(
                kanji="研究", known_status=_("already-known") + "\\(✓\\)"
            ),
        ),
        IO(
            "u",
            _("toggled-the-{known_status}-of-{kanji}").format(
                kanji="研究", known_status=_("unknown")
            ),
        ),
        # Each command and undo/redo.
        IO("h", f'{_("usage")}:.*{_("help-quit")}'),
        IO("l 研究", "けんきゅう \\(研究\\) : study/research/investigation"),
        IO("l asdasd", _("nothing-found")),
        IO("新しい", _("nothing-found")),
        IO("a 新しい", f'{_("found")}: \\(1\\)\n     1 0100 新しい'),
        IO("新しい", f'{_("found")}:.*1 0100 新しい'),
        IO("c 新しい 別", f'{_("found")}: \\(1\\)\n     1 0100 別'),
        IO("別", f'{_("found")}: \\(1\\)\n     1 0100 別'),
        IO(
            "u",
            _("{new_kanji}-changed-back-to-{kanji}").format(kanji="新しい", new_kanji="別"),
        ),
        IO("r", _("{kanji}-changed-to-{new_kanji}").format(kanji="新しい", new_kanji="別")),
        IO(
            "u",
            _("{new_kanji}-changed-back-to-{kanji}").format(kanji="新しい", new_kanji="別"),
        ),
        IO(
            "u",
            _("{kanji}-has-been-deleted-from-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO(
            "r",
            _("{kanji}-added-to-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO("d 新しい", _("{kanji}-deleted").format(kanji="新しい")),
        IO(
            "u",
            _("{kanji}-added-to-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO(
            "r",
            _("{kanji}-has-been-deleted-from-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO(
            "u",
            _("{kanji}-added-to-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO("ak 新しい べつ", f'{_("found")}: \\(1\\).*1 0100 新しい 1 あたらしい 2 べつ'),
        IO("u", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="べつ")),
        IO("r", _("{kana}-added-to-{kanji}").format(kanji="新しい", kana="べつ")),
        IO(
            "dk 新しい べつ", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="べつ")
        ),
        IO("u", _("{kana}-added-to-{kanji}").format(kanji="新しい", kana="べつ")),
        IO("r", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="べつ")),
        IO(
            "i",
            f'{_("info")}:\n  {_("known")}: 0\n  {_("learning")}: 6\n  {_("total")}: 6',
        ),
        IO("t 新しい", f'{_("found")}: \\(1\\)\n     1 0100 新しい 1 あたらしい ✓'),
        IO(
            "i",
            f'{_("info")}:\n  {_("known")}: 1\n  {_("learning")}: 5\n  {_("total")}: 6',
        ),
        IO("t 新しい", f'{_("found")}: \\(1\\)\n     1 0100 新しい 1 あたらしい[^✓]+$'),
        IO(
            "i",
            f'{_("info")}:\n  {_("known")}: 0\n  {_("learning")}: 6\n  {_("total")}: 6',
        ),
        IO("d 新しい", _("{kanji}-deleted").format(kanji="新しい")),
        # Indexes.
        IO("新しい", _("nothing-found")),
        IO("a 新しい", "1 0100 新しい 1 あたらしい"),
        IO("ak 1 かな", "1 0100 新しい 1 あたらしい 2 かな"),
        IO("ak 1 かなに", "1 0100 新しい 1 あたらしい 2 かな 3 かなに"),
        IO("ak 1 かなさん", "1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん"),
        IO("ck ああああ いいいい　うううう", _("{kanji}-not-found").format(kanji="ああああ")),
        IO("ck 1 かなに かなよん", "1 0100 新しい 1 あたらしい 2 かな 3 かなよん 4 かなさん"),
        IO(
            "u",
            _("{new_kana}-changed-back-to-{kana}-for-{kanji}").format(
                kanji="新しい", kana="かなに", new_kana="かなよん"
            ),
        ),
        IO(
            "r",
            _("{kana}-changed-to-{new_kana}-for-{kanji}").format(
                kanji="新しい", kana="かなに", new_kana="かなよん"
            ),
        ),
        IO(
            "u",
            _("{new_kana}-changed-back-to-{kana}-for-{kanji}").format(
                kanji="新しい", kana="かなに", new_kana="かなよん"
            ),
        ),
        IO("新しい", "1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん"),
        IO("t 1", "1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん ✓"),
        IO("t 1", "1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん[^✓]+$"),
        IO("dk 1 3", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="かなに")),
        IO("新しい", "1 0100 新しい 1 あたらしい 2 かな 3 かなさん"),
        IO("dk 1 3", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="かなさん")),
        IO("新しい", "1 0100 新しい 1 あたらしい 2 かな"),
        IO("dk 1 2", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="かな")),
        IO("新しい", "1 0100 新しい"),
        IO("c 1 別", f'{_("found")}: \\(1\\)\n     1 0100 別'),
        IO("別", f'{_("found")}: \\(1\\)\n     1 0100 別'),
        IO(
            "u",
            _("{new_kanji}-changed-back-to-{kanji}").format(kanji="新しい", new_kanji="別"),
        ),
        IO("新しい", f'{_("found")}: \\(1\\)\n     1 0100 新しい'),
        IO("d 1", _("{kanji}-deleted").format(kanji="新しい")),
        # ('新しい', _('nothing-found')),
        IO(
            "u",
            _("{kanji}-added-to-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO("u", _("{kana}-added-to-{kanji}").format(kanji="新しい", kana="かな")),
        IO("u", _("{kana}-added-to-{kanji}").format(kanji="新しい", kana="かなさん")),
        IO("u", _("{kana}-added-to-{kanji}").format(kanji="新しい", kana="かなに")),
        IO(
            "u",
            _("toggled-the-{known_status}-of-{kanji}").format(
                kanji="新しい", known_status=_("already-known") + "\\(✓\\)"
            ),
        ),
        IO(
            "u",
            _("toggled-the-{known_status}-of-{kanji}").format(
                kanji="新しい", known_status=_("unknown")
            ),
        ),
        IO("u", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="かなさん")),
        IO("u", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="かなに")),
        IO("u", _("{kana}-deleted-from-{kanji}").format(kanji="新しい", kana="かな")),
        IO(
            "u",
            _("{kanji}-has-been-deleted-from-list-{list_name}").format(
                kanji="新しい", list_name="0100"
            ),
        ),
        IO("新しい", _("nothing-found")),
        # Each command's error messages.
        IO("a 新しい", f'{_("found")}: \\(1\\)\n     1 0100 新しい'),
        IO("a 新しい", _("{kanji}-already-exists").format(kanji="新しい")),
        IO("c 新しい二 新しい", _("{kanji}-not-found").format(kanji="新しい二")),
        IO("c 新しい 新しい", _("{kanji}-already-exists").format(kanji="新しい")),
        IO("d 新しい二", _("{kanji}-not-found").format(kanji="新しい二")),
        IO("ak 新しい かな", f'{_("found")}: \\(1\\)\n     1 0100 新しい 1 あたらしい 2 かな'),
        IO(
            "ak 新しい かな",
            _("{kana}-already-exists-for-{kanji}").format(kanji="新しい", kana="かな"),
        ),
        IO(
            "ck 新しい かなに かなさん",
            _("{kana}-not-found-for-{kanji}").format(kanji="新しい", kana="かなに"),
        ),
        IO(
            "ck 新しい かな かな",
            _("{kana}-already-exists-for-{kanji}").format(kanji="新しい", kana="かな"),
        ),
        IO(
            "dk 新しい かなに",
            _("{kana}-not-found-for-{kanji}").format(kanji="新しい", kana="かなに"),
        ),
        IO("t 新しい二", _("{kanji}-not-found").format(kanji="新しい二")),
        IO("あああああ", _("nothing-found")),
        IO("a あああああ", f'{_("found")}: \\(1\\)\n     1 0100 あああああ'),
        IO("かかかかか", _("nothing-found")),
        IO("a 0", f'{_("found")}: \\(1\\)\n     1 0100 かかかかか'),
    ]


@pytest.mark.parametrize(
    "locale",
    [
        None,
        ("ja"),
        ("en"),
        ("es"),
        ("fr"),
    ],
)
def test_usage(locale: str | None) -> None:
    do_usage(locale, __io_general)


def __io_change_lang() -> list[IO]:
    return [
        IO("ja", ""),  # No output from the language change.
        IO("asdasd", "検索.*何も見つからない。"),  # Output is from the subsequent prompt.
        IO("en", ""),
        IO("asdasd", "Search.*Nothing found."),
        IO("es", ""),
        IO("asdasd", "Buscar.*Nada encontrado."),
        IO("fr", ""),
        IO("asdasd", "Chercher.*Rien trouvé."),
    ]


@pytest.mark.parametrize(
    "locale",
    [
        None,
        ("ja"),
        ("en"),
        ("es"),
        ("fr"),
    ],
)
def test_change_lang(locale: str | None) -> None:
    do_usage(locale, __io_change_lang)


def __io_save() -> list[IO]:
    return [
        IO("s", ""),
    ]


def test_save() -> None:
    do_usage(None, __io_save)


def __io_quit() -> list[IO]:
    return [
        IO("q", ""),
    ]


def test_quit() -> None:
    try:
        do_usage(None, __io_quit)
    except SystemExit as e:
        assert e.code == 0


def do_usage(locale: str | None, test_io: Callable[[], list[IO]]) -> None:
    if locale is None:
        unset_locale()
    else:
        set_locale(locale)
    stdin = sys.stdin
    stdout = sys.stdout
    sys.stdin = StringIO()
    sys.stdout = StringIO()
    try:
        vocab = Vocab("tests/test_data/vocab_good.csv")
        vocab.filename = os.devnull  # Saves don't change the original file.
        command_stack = CommandStack()
        previous_search: str = ""
        kanji_found: list[str] = []
        for io in test_io():
            sys.stdin.seek(0)
            sys.stdout.seek(0)
            sys.stdin.truncate(0)
            sys.stdout.truncate(0)
            sys.stdin.write(io.test_input + "\n")
            sys.stdin.seek(0)
            previous_search, kanji_found = main_stuff(
                vocab, command_stack, previous_search, kanji_found
            )
            sys.stdout.seek(0)
            actual_output = strip_ansi_terminal_escapes(sys.stdout.read())
            if not re.search(io.expected_output_regex, actual_output, re.S):
                print(
                    "Expected: " + io.expected_output_regex, file=sys.stderr
                )  # pragma: no cover
                print("Actual: " + actual_output, file=sys.stderr)  # pragma: no cover
            assert re.compile(io.expected_output_regex, re.S).search(actual_output)
    finally:
        sys.stdin = stdin
        sys.stdout = stdout


@pytest.mark.parametrize(
    "locale",
    [
        None,
        ("ja"),
        ("en"),
        ("es"),
        ("fr"),
    ],
)
def test_remaining_translations_with_interpolations(locale: str | None) -> None:
    if locale is None:
        unset_locale()
    else:
        assert isinstance(locale, str)  # for mypy
        set_locale(locale)
    # This will explode if they have a typo in the
    # interpolated variables in the translation.
    _("{vocab_file}-failed-to-read-{e}").format(vocab_file="bogus.csv", e=Exception())
    _("{vocab_file}-failed-to-write-{e}").format(vocab_file="bogus.csv", e=Exception())


def test_is_kanji_or_kana() -> None:
    assert is_kanji_or_kana("多")
    assert is_kanji_or_kana("々")  # Is used in writing words.
    assert is_kanji_or_kana("多々")
    assert is_kanji_or_kana("た")
    assert is_kanji_or_kana("タ")
    assert is_kanji_or_kana("〇")  # For this purpose is a word.
    assert not is_kanji_or_kana("。")  # Other punctuation is not part of words.
    assert not is_kanji_or_kana("t")
    assert not is_kanji_or_kana("-")
    assert not is_kanji_or_kana("0")
