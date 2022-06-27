import contextlib
import re
import sys
import unittest
from colors import color
from io import StringIO
from nevsjapanesevocab import main_stuff, replace_indices
from unittest_data_provider import data_provider
from commands import CommandStack
from vocab import Vocab

# English words will never exist in the real data. I'm taking
# advantage of that to allow the tests to expect things
# not to exist, or that make modifications to not rely on
# the existing data.


class MainTestCase(unittest.TestCase):

    def setUp(self):
        self.vocab = Vocab('src/tests/test_data/vocab_good.csv')
        self.vocab.add('new')
        self.vocab.add('new2')
        self.vocab.add('new3')
        self.vocab.add_kana('new2', 'kana1')
        self.vocab.add_kana('new2', 'kana2')
        self.vocab.add_kana('new2', 'kana3')

    # TODO: index 0
    def replace_indices():
        return [
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

    @data_provider(replace_indices)
    def test_replace_indices(self, search, params, expected_result):
        found_kanji = self.vocab.search(search)
        self.assertEqual(replace_indices(
            self.vocab, '', found_kanji, params), expected_result)

    __io = [
        # Search found and not found.
        ('研究', '見つかった: \\(1\\)\n     1 0100 研究 1 けんきゅう'),
        ('notfound', '何も見つからない。'),
        # Each command's usage when used with incorrect
        # parameters or at the wrong time.
        ('l', '使い方: l <漢字|仮名>'),
        ('a', '使い方: a <漢字>\n何も見つからない。'),
        ('d', '使い方: d <漢字>\n何も見つからない。'),
        ('ak', '使い方: a <漢字> <仮名>\n何も見つからない。'),
        ('ak new', '使い方: a <漢字> <仮名>\n何も見つからない。'),
        ('dk', '使い方: d <漢字> <仮名>\n何も見つからない。'),
        ('dk new', '使い方: d <漢字> <仮名>\n何も見つからない。'),
        ('t', '使い方: t <漢字>\n何も見つからない。'),
        ('u', '元に戻すものがない。'),
        ('r', '遣り直しものがない。'),
        # Each command and undo/redo.
        ('h', '使い方:.*終了'),
        ('l 研究', 'けんきゅう \\(研究\\) : study/research/investigation'),
        ('new', '何も見つからない。'),
        ('a new', '見つかった: \\(1\\)\n     1 0100 new'),
        ('new', '見つかった.*1 0100 new'),
        ('c new NEW', '見つかった: \\(1\\)\n     1 0100 NEW'),
        ('NEW', '見つかった: \\(1\\)\n     1 0100 NEW'),
        ('u', 'NEWをnewに戻した。'),
        ('u', 'newはリスト0100から削除した。'),
        ('r', 'newはリスト0100に追加した。'),
        ('d new', 'newは削除した。'),
        ('u', 'newはリスト0100に追加した。'),
        ('r', 'newはリスト0100から削除した。'),
        ('u', 'newはリスト0100に追加した。'),
        ('ak new kana', '見つかった: \\(1\\).*1 0100 new 1 kana'),
        ('u', 'kanaはnewから削除した。'),
        ('r', 'kanaはnewに追加した。'),
        ('dk new kana', 'newはkanaが削除した。'),
        ('u', 'kanaはnewに追加した。'),
        ('r', 'kanaはnewから削除した。'),
        ('u', 'kanaはnewに追加した。'),
        ('k', 'データ:\n  分かった: 0\n  学んでいる 6\n  合計: 6'),
        ('t new', '見つかった: \\(1\\)\n     1 0100 new 1 kana ✓'),
        ('k', 'データ:\n  分かった: 1\n  学んでいる 5\n  合計: 6'),
        ('t new', '見つかった: \\(1\\)\n     1 0100 new 1 kana[^✓]+$'),
        ('k', 'データ:\n  分かった: 0\n  学んでいる 6\n  合計: 6'),
        ('d new', 'newは削除した。'),
        # Indexes.
        ('new', '何も見つからない。'),
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
        ('c 1 NEW', '見つかった: \\(1\\)\n     1 0100 NEW'),
        ('NEW', '見つかった: \\(1\\)\n     1 0100 NEW'),
        ('u', 'NEWをnewに戻した。'),
        ('new', '見つかった: \\(1\\)\n     1 0100 new'),
        ('d 1', 'newは削除した。'),
        ('new', '何も見つからない。'),
        ('u', 'newはリスト0100に追加した。'),
        ('u', 'kanaはnewに追加した。'),
        ('u', 'kana3はnewに追加した。'),
        ('u', 'kana2はnewに追加した。'),
        ('u', 'newのステータスが既知\\(✓\\)に変更された。'),
        ('u', 'newのステータスが未知に変更された。'),
        ('u', 'kana3はnewから削除した。'),
        ('u', 'kana2はnewから削除した。'),
        ('u', 'kanaはnewから削除した。'),
        ('u', 'newはリスト0100から削除した。'),
        ('new', '何も見つからない。'),
        # Each aommand's error messages.
        ('a new', '見つかった: \\(1\\)\n     1 0100 new'),
        ('a new', 'newは既に有る。'),
        ('c new2 new', 'new2は見つからない。'),
        ('c new new', 'newは既に有る。'),
        ('d new2', 'new2は見つからない。'),
        ('ak new kana', '見つかった: \\(1\\)\n     1 0100 new 1 kana'),
        ('ak new kana', 'newはkanaが既に有る。'),
        ('ck new kana2 kana3', 'newはkana2が見つからない。'),
        ('ck new kana kana', 'newはkanaが既に有る。'),
        ('dk new kana2', 'newはkana2が見つからない。'),
        ('t new2', 'new2は見つからない。'),
    ]

    def test_usage(self):
        stdin = sys.stdin
        stdout = sys.stdout
        sys.stdin = StringIO()
        sys.stdout = StringIO()
        try:
            vocab = Vocab('src/tests/test_data/vocab_good.csv')
            command_stack = CommandStack()
            kanji_found = []
            for test_input, expected_regex in self.__io:
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
                actual_output = MainTestCase.__stripEscape(sys.stdout.read())
                if not re.search(expected_regex, actual_output, re.S):
                    print('Expected: ' + expected_regex, file=sys.stderr)
                    print('Actual: ' + actual_output, file=sys.stderr)
                self.assertRegex(
                    actual_output, re.compile(
                        expected_regex, re.S))
        finally:
            sys.stdin = stdin
            sys.stdout = stdout

    def __stripEscape(s):
        return re.sub('\x1b\\[[\\d;]+m', '', s)
