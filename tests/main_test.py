import contextlib
import pytest
import re
import sys
from colors import color  # type: ignore
from commands import CommandStack
from io import StringIO
from nevsjapanesevocab import main_stuff, replace_indices
from typing import List, Tuple
from unittest_data_provider import data_provider  # type: ignore
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    vocab = Vocab('tests/test_data/vocab_good.csv')
    vocab.add('new')
    vocab.add('new2')
    vocab.add('new3')
    vocab.add_kana('new2', 'kana1')
    vocab.add_kana('new2', 'kana2')
    vocab.add_kana('new2', 'kana3')
    return vocab


@pytest.mark.parametrize("search, params, expected_result",
                         [
                             ('new', ['n', '-50'], ['n', '-50']),
                             ('new', ['n', '-1'], ['n', '-1']),
                             ('new', ['n', '0'], ['n', '0']),
                             ('new', ['n', '1'], ['n', 'new']),
                             ('new', ['n', '2'], ['n', 'new2']),
                             ('new', ['n', '3'], ['n', 'new3']),
                             ('new', ['n', '4'], ['n', '4']),
                             ('new', ['n', '999'], ['n', '999']),
                             ('new', ['n', '1', '1'], ['n', 'new', '1']),
                             ('new', ['n', '2', '-50'], ['n', 'new2', '-50']),
                             ('new', ['n', '2', '-1'], ['n', 'new2', '-1']),
                             ('new', ['n', '2', '0'], ['n', 'new2', '0']),
                             ('new', ['n', '2', '1'], ['n', 'new2', 'kana1']),
                             ('new', ['n', '2', '2'], ['n', 'new2', 'kana2']),
                             ('new', ['n', '2', '3'], ['n', 'new2', 'kana3']),
                             ('new', ['n', '2', '4'], ['n', 'new2', '4']),
                             ('new', ['n', '2', '999'], ['n', 'new2', '999']),
                         ]
                         )
def test_replace_indices(
        vocab: Vocab,
        search: str,
        params: List[str],
        expected_result: List[str]) -> None:
    found_kanji = vocab.search(search)
    assert replace_indices(vocab, '', found_kanji, params) == expected_result


__io = [
    ('\n', 'search'),
    # Search found and not found.
    ('研究', 'found: \\(1\\)\n     1 0100 研究 1 けんきゅう'),
    ('notfound', 'nothing-found'),
    # Each command's usage when used with incorrect
    # parameters or at the wrong time.
    ('l', '使い方: l <漢字|仮名>'),
    ('a', '使い方: a <漢字>\nnothing-found'),
    ('d', '使い方: d <漢字>\nnothing-found'),
    ('ak', '使い方: a <漢字> <仮名>\nnothing-found'),
    ('ak new', '使い方: a <漢字> <仮名>\nnothing-found'),
    ('dk', '使い方: d <漢字> <仮名>\nnothing-found'),
    ('dk new', '使い方: d <漢字> <仮名>\nnothing-found'),
    ('t', '使い方: t <漢字>\nnothing-found'),
    ('u', '元に戻すものがない。'),
    ('r', '遣り直しものがない。'),
    # Each command and undo/redo.
    ('h', '使い方:.*終了'),
    ('l 研究', 'けんきゅう \\(研究\\) : study/research/investigation'),
    ('new', 'nothing-found'),
    ('a new', 'found: \\(1\\)\n     1 0100 new'),
    ('new', 'found.*1 0100 new'),
    ('c new NEW', 'found: \\(1\\)\n     1 0100 NEW'),
    ('NEW', 'found: \\(1\\)\n     1 0100 NEW'),
    ('u', 'NEWをnewに戻した。'),
    ('u', 'new-has-been-deleted-from-list-0100'),
    ('r', 'newはリスト0100に追加した。'),
    ('d new', 'newは削除した。'),
    ('u', 'newはリスト0100に追加した。'),
    ('r', 'new-has-been-deleted-from-list-0100'),
    ('u', 'newはリスト0100に追加した。'),
    ('ak new kana', 'found: \\(1\\).*1 0100 new 1 kana'),
    ('u', 'kanaはnewから削除した。'),
    ('r', 'kanaはnewに追加した。'),
    ('dk new kana', 'newはkanaが削除した。'),
    ('u', 'kanaはnewに追加した。'),
    ('r', 'kanaはnewから削除した。'),
    ('u', 'kanaはnewに追加した。'),
    ('k', 'データ:\n  分かった: 0\n  学んでいる 6\n  合計: 6'),
    ('t new', 'found: \\(1\\)\n     1 0100 new 1 kana ✓'),
    ('k', 'データ:\n  分かった: 1\n  学んでいる 5\n  合計: 6'),
    ('t new', 'found: \\(1\\)\n     1 0100 new 1 kana[^✓]+$'),
    ('k', 'データ:\n  分かった: 0\n  学んでいる 6\n  合計: 6'),
    ('d new', 'newは削除した。'),
    # Indexes.
    ('new', 'nothing-found'),
    ('a new', '1 0100 new'),
    ('ak 1 kana', '1 0100 new 1 kana'),
    ('ak 1 kana2', '1 0100 new 1 kana 2 kana2'),
    ('ak 1 kana3', '1 0100 new 1 kana 2 kana2 3 kana3'),
    ('ck 1 kana2 kana4', '1 0100 new 1 kana 2 kana4 3 kana3'),
    ('u', 'newはkana4をkana2に戻した。'),
    ('new', '1 0100 new 1 kana 2 kana2 3 kana3'),
    ('t 1', '1 0100 new 1 kana 2 kana2 3 kana3 ✓'),
    ('t 1', '1 0100 new 1 kana 2 kana2 3 kana3[^✓]+$'),
    ('dk 1 2', 'newはkana2が削除した。'),
    ('new', '1 0100 new 1 kana 2 kana3'),
    ('dk 1 2', 'newはkana3が削除した。'),
    ('new', '1 0100 new 1 kana'),
    ('dk 1 1', 'newはkanaが削除した。'),
    ('new', '1 0100 new'),
    ('c 1 NEW', 'found: \\(1\\)\n     1 0100 NEW'),
    ('NEW', 'found: \\(1\\)\n     1 0100 NEW'),
    ('u', 'NEWをnewに戻した。'),
    ('new', 'found: \\(1\\)\n     1 0100 new'),
    ('d 1', 'newは削除した。'),
    ('new', 'nothing-found'),
    ('u', 'newはリスト0100に追加した。'),
    ('u', 'kanaはnewに追加した。'),
    ('u', 'kana3はnewに追加した。'),
    ('u', 'kana2はnewに追加した。'),
    ('u', 'newのステータスが既知\\(✓\\)に変更された。'),
    ('u', 'newのステータスが未知に変更された。'),
    ('u', 'kana3はnewから削除した。'),
    ('u', 'kana2はnewから削除した。'),
    ('u', 'kanaはnewから削除した。'),
    ('u', 'new-has-been-deleted-from-list-0100'),
    ('new', 'nothing-found'),
    # Each aommand's error messages.
    ('a new', 'found: \\(1\\)\n     1 0100 new'),
    ('a new', 'newは既に有る。'),
    ('c new2 new', 'new2は見つからない。'),
    ('c new new', 'newは既に有る。'),
    ('d new2', 'new2は見つからない。'),
    ('ak new kana', 'found: \\(1\\)\n     1 0100 new 1 kana'),
    ('ak new kana', 'newはkanaが既に有る。'),
    ('ck new kana2 kana3', 'newはkana2が見つからない。'),
    ('ck new kana kana', 'newはkanaが既に有る。'),
    ('dk new kana2', 'newはkana2が見つからない。'),
    ('t new2', 'new2は見つからない。'),
]


def test_usage() -> None:
    stdin = sys.stdin
    stdout = sys.stdout
    sys.stdin = StringIO()
    sys.stdout = StringIO()
    try:
        vocab = Vocab('tests/test_data/vocab_good.csv')
        command_stack = CommandStack()
        kanji_found: List[str] = []
        for test_input, expected_regex in __io:
            sys.stdin.seek(0)
            sys.stdout.seek(0)
            sys.stdin.truncate(0)
            sys.stdout.truncate(0)
            sys.stdin.write(test_input + '\n')
            sys.stdin.seek(0)
            search, kanji_found = main_stuff(
                vocab, command_stack, '', kanji_found
            )
            sys.stdout.seek(0)
            actual_output = __stripEscapes(sys.stdout.read())
            if not re.search(expected_regex, actual_output, re.S):
                print('Expected: ' + expected_regex, file=sys.stderr)
                print('Actual: ' + actual_output, file=sys.stderr)
            assert re.compile(expected_regex, re.S).search(actual_output)
    finally:
        sys.stdin = stdin
        sys.stdout = stdout


def __stripEscapes(s: str) -> str:
    return re.sub('\x1b\\[[\\d;]+m', '', s)
