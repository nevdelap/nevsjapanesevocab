import contextlib
import pytest
import re
import sys
from colors import color  # type: ignore
from commands import CommandStack
from io import StringIO
from localisation import _, set_locale, unset_locale
from nevsjapanesevocab import main_stuff, replace_indices
from test_helpers import strip_ansi_terminal_escapes
from typing import List, Optional, Tuple
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    vocab = Vocab('tests/test_data/vocab_good.csv')
    vocab.add('新しい')
    vocab.add('新しい二')
    vocab.add('新しい三')
    vocab.add_kana('新しい二', 'かなに')
    vocab.add_kana('新しい二', 'かなさん')
    return vocab


@pytest.mark.parametrize('search, params, expected_result',
                         [
                             ('新しい', ['-50'], []),
                             ('新しい', ['-1'], []),
                             ('新しい', ['0'], ['あああああ']),
                             ('新しい', ['1'], ['新しい']),
                             ('新しい', ['2'], ['新しい二']),
                             ('新しい', ['3'], ['新しい三']),
                             ('新しい', ['4'], []),
                             ('新しい', ['999'], []),
                             ('新しい', ['1', '1'], ['新しい', 'あたらしい']),
                             ('新しい', ['新しい', '1'], ['新しい', 'あたらしい']),
                             ('新しい', ['2', '-50'], ['新しい二']),
                             ('新しい', ['2', '-1'], ['新しい二']),
                             ('新しい', ['2', '0'], ['新しい二']),
                             ('新しい', ['2', '1'], ['新しい二', 'あたらしいに']),
                             ('新しい', ['2', '2'], ['新しい二', 'かなに']),
                             ('新しい', ['2', '3'], ['新しい二', 'かなさん']),
                             ('新しい', ['2', '4'], ['新しい二']),
                             ('新しい', ['2', '999'], ['新しい二']),
                             ('新しい', ['新しい二', '-50'], ['新しい二']),
                             ('新しい', ['新しい二', '-1'], ['新しい二']),
                             ('新しい', ['新しい二', '0'], ['新しい二']),
                             ('新しい', ['新しい二', '1'], ['新しい二', 'あたらしいに']),
                             ('新しい', ['新しい二', '2'], ['新しい二', 'かなに']),
                             ('新しい', ['新しい二', '3'], ['新しい二', 'かなさん']),
                             ('新しい', ['新しい二', '4'], ['新しい二']),
                             ('新しい', ['新しい二', '999'], ['新しい二']),
                         ]
                         )
def test_replace_indices(
        vocab: Vocab,
        search: str,
        params: list[str],
        expected_result: list[str]) -> None:
    found_kanji = vocab.search(search)
    assert replace_indices(
        vocab,
        'あああああ',
        found_kanji,
        params,
        False) == expected_result

# This has examples of all translations to ensure that the
# translations themselves are syntactically correct in
# regards to interpolation. E.g. {new_kanji}, not
# {new-kanji}.


def __io() -> list[tuple[str, str]]:
    return [
        ('\n', _('search')),
        # Bad command.
        ('w 漢字 かな', _('usage-h-to-show-usage')),
        # Bad usage.
        ('t', f'{_("usage")}: t {_("kanji")}'),
        # Attempt add previous search when there is not previous search.
        ('a 0', f'{_("usage")}: a {_("kanji")}'),
        # Search found and not found.
        ('研究', f'{_("found")}: \\(1\\)\n     1 0100 研究 1 けんきゅう'),
        ('あああああ', _('nothing-found')),
        # Each command's usage when used with incorrect
        # parameters or at the wrong time.
        ('l', f'{_("usage")}: l {_("kanji")}|{_("kana")}'),
        ('a', f'{_("usage")}: a {_("kanji")}'),
        ('d', f'{_("usage")}: d {_("kanji")}'),
        ('ak', f'{_("usage")}: a {_("kanji")}{_("space")}{_("kana")}\n'),
        ('ak new', f'{_("usage")}: a {_("kanji")}{_("space")}{_("kana")}'),
        ('dk', f'{_("usage")}: d {_("kanji")}{_("space")}{_("kana")}'),
        ('dk new', f'{_("usage")}: d {_("kanji")}{_("space")}{_("kana")}'),
        ('u', _('there-is-nothing-to-undo')),
        ('r', _('there-is-nothing-to-redo')),
        # Toggle status.
        ('t 研究', f'{_("found")}: \\(1\\)\n     1 0100 研究 1 けんきゅう ' + '✓'),
        ('u',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='研究',
                                                           known_status=_('unknown'))),
        ('r',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='研究',
                                                           known_status=_('already-known') + '\\(✓\\)')),
        ('u',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='研究',
                                                           known_status=_('unknown'))),
        # Each command and undo/redo.
        ('h', f'{_("usage")}:.*{_("help-quit")}'),
        ('l 研究', 'けんきゅう \\(研究\\) : study/research/investigation'),
        ('l asdasd', _('nothing-found')),
        ('新しい', _('nothing-found')),
        ('a 新しい', f'{_("found")}: \\(1\\)\n     1 0100 新しい'),
        ('新しい', f'{_("found")}:.*1 0100 新しい'),
        ('c 新しい 別', f'{_("found")}: \\(1\\)\n     1 0100 別'),
        ('別', f'{_("found")}: \\(1\\)\n     1 0100 別'),
        ('u',
         _('{new_kanji}-changed-back-to-{kanji}').format(kanji='新しい',
                                                         new_kanji='別')),
        ('r', _('{kanji}-changed-to-{new_kanji}').format(kanji='新しい', new_kanji='別')),
        ('u',
         _('{new_kanji}-changed-back-to-{kanji}').format(kanji='新しい',
                                                         new_kanji='別')),
        ('u',
         _('{kanji}-has-been-deleted-from-list-{list_name}').format(kanji='新しい',
                                                                    list_name='0100')),
        ('r',
         _('{kanji}-added-to-list-{list_name}').format(kanji='新しい',
                                                       list_name='0100')),
        ('d 新しい', _('{kanji}-deleted').format(kanji='新しい')),
        ('u',
         _('{kanji}-added-to-list-{list_name}').format(kanji='新しい',
                                                       list_name='0100')),
        ('r',
         _('{kanji}-has-been-deleted-from-list-{list_name}').format(kanji='新しい',
                                                                    list_name='0100')),
        ('u',
         _('{kanji}-added-to-list-{list_name}').format(kanji='新しい',
                                                       list_name='0100')),
        ('ak 新しい べつ', f'{_("found")}: \\(1\\).*1 0100 新しい 1 あたらしい 2 べつ'),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='べつ')),
        ('r', _('{kana}-added-to-{kanji}').format(kanji='新しい', kana='べつ')),
        ('dk 新しい べつ', _(
            '{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='べつ')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='新しい', kana='べつ')),
        ('r', _('{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='べつ')),
        ('i', f'{_("info")}:\n  {_("known")}: 0\n  {_("learning")}: 6\n  {_("total")}: 6'),
        ('t 新しい', f'{_("found")}: \\(1\\)\n     1 0100 新しい 1 あたらしい ✓'),
        ('i', f'{_("info")}:\n  {_("known")}: 1\n  {_("learning")}: 5\n  {_("total")}: 6'),
        ('t 新しい', f'{_("found")}: \\(1\\)\n     1 0100 新しい 1 あたらしい[^✓]+$'),
        ('i', f'{_("info")}:\n  {_("known")}: 0\n  {_("learning")}: 6\n  {_("total")}: 6'),
        ('d 新しい', _('{kanji}-deleted').format(kanji='新しい')),
        # Indexes.
        ('新しい', _('nothing-found')),
        ('a 新しい', '1 0100 新しい 1 あたらしい'),
        ('ak 1 かな', '1 0100 新しい 1 あたらしい 2 かな'),
        ('ak 1 かなに', '1 0100 新しい 1 あたらしい 2 かな 3 かなに'),
        ('ak 1 かなさん', '1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん'),
        ('ck 1 かなに かなよん', '1 0100 新しい 1 あたらしい 2 かな 3 かなよん 4 かなさん'),
        ('u',
         _('{new_kana}-changed-back-to-{kana}-for-{kanji}').format(kanji='新しい',
                                                                   kana='かなに',
                                                                   new_kana='かなよん')),
        ('r',
         _('{kana}-changed-to-{new_kana}-for-{kanji}').format(kanji='新しい',
                                                              kana='かなに',
                                                              new_kana='かなよん')),
        ('u',
         _('{new_kana}-changed-back-to-{kana}-for-{kanji}').format(kanji='新しい',
                                                                   kana='かなに',
                                                                   new_kana='かなよん')),
        ('新しい', '1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん'),
        ('t 1', '1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん ✓'),
        ('t 1', '1 0100 新しい 1 あたらしい 2 かな 3 かなに 4 かなさん[^✓]+$'),
        ('dk 1 3',
         _('{kana}-deleted-from-{kanji}').format(kanji='新しい',
                                                 kana='かなに')),
        ('新しい', '1 0100 新しい 1 あたらしい 2 かな 3 かなさん'),
        ('dk 1 3',
         _('{kana}-deleted-from-{kanji}').format(kanji='新しい',
                                                 kana='かなさん')),
        ('新しい', '1 0100 新しい 1 あたらしい 2 かな'),
        ('dk 1 2', _(
            '{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='かな')),
        ('新しい', '1 0100 新しい'),
        ('c 1 別', f'{_("found")}: \\(1\\)\n     1 0100 別'),
        ('別', f'{_("found")}: \\(1\\)\n     1 0100 別'),
        ('u',
         _('{new_kanji}-changed-back-to-{kanji}').format(kanji='新しい',
                                                         new_kanji='別')),
        ('新しい', f'{_("found")}: \\(1\\)\n     1 0100 新しい'),
        ('d 1', _('{kanji}-deleted').format(kanji='新しい')),
        # ('新しい', _('nothing-found')),
        ('u',
         _('{kanji}-added-to-list-{list_name}').format(kanji='新しい',
                                                       list_name='0100')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='新しい', kana='かな')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='新しい', kana='かなさん')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='新しい', kana='かなに')),
        ('u',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='新しい',
                                                           known_status=_('already-known') + '\\(✓\\)')),
        ('u',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='新しい',
                                                           known_status=_('unknown'))),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='かなさん')),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='かなに')),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='新しい', kana='かな')),
        ('u',
         _('{kanji}-has-been-deleted-from-list-{list_name}').format(kanji='新しい',
                                                                    list_name='0100')),
        ('新しい', _('nothing-found')),
        # Each command's error messages.
        ('a 新しい', f'{_("found")}: \\(1\\)\n     1 0100 新しい'),
        ('a 新しい', _('{kanji}-already-exists').format(kanji='新しい')),
        ('c 新しい二 新しい', _('{kanji}-not-found').format(kanji='新しい二')),
        ('c 新しい 新しい', _('{kanji}-already-exists').format(kanji='新しい')),
        ('d 新しい二', _('{kanji}-not-found').format(kanji='新しい二')),
        ('ak 新しい かな', f'{_("found")}: \\(1\\)\n     1 0100 新しい 1 あたらしい 2 かな'),
        ('ak 新しい かな', _(
            '{kana}-already-exists-for-{kanji}').format(kanji='新しい', kana='かな')),
        ('ck 新しい かなに かなさん', _(
            '{kana}-not-found-for-{kanji}').format(kanji='新しい', kana='かなに')),
        ('ck 新しい かな かな', _(
            '{kana}-already-exists-for-{kanji}').format(kanji='新しい', kana='かな')),
        ('dk 新しい かなに', _(
            '{kana}-not-found-for-{kanji}').format(kanji='新しい', kana='かなに')),
        ('t 新しい二', _('{kanji}-not-found').format(kanji='新しい二')),
        ('あああああ', _('nothing-found')),
        ('a あああああ', f'{_("found")}: \\(1\\)\n     1 0100 あああああ'),
        ('かかかかか', _('nothing-found')),
        ('a 0', f'{_("found")}: \\(1\\)\n     1 0100 かかかかか'),
    ]


@pytest.mark.parametrize('locale',
                         [
                             None,
                             ('ja'),
                             ('en'),
                             ('es'),
                             ('fr'),
                         ]
                         )
def test_usage(locale: Optional[str]) -> None:
    if locale is None:
        unset_locale()
    else:
        assert isinstance(locale, str)  # for mypy
        set_locale(locale)
    stdin = sys.stdin
    stdout = sys.stdout
    sys.stdin = StringIO()
    sys.stdout = StringIO()
    try:
        vocab = Vocab('tests/test_data/vocab_good.csv')
        command_stack = CommandStack()
        previous_search: Optional[str] = None
        kanji_found: list[str] = []
        for test_input, expected_regex in __io():
            sys.stdin.seek(0)
            sys.stdout.seek(0)
            sys.stdin.truncate(0)
            sys.stdout.truncate(0)
            sys.stdin.write(test_input + '\n')
            sys.stdin.seek(0)
            previous_search, kanji_found = main_stuff(
                vocab, command_stack, previous_search, kanji_found
            )
            sys.stdout.seek(0)
            actual_output = strip_ansi_terminal_escapes(sys.stdout.read())
            if not re.search(expected_regex, actual_output, re.S):
                print('Expected: ' + expected_regex, file=sys.stderr)
                print('Actual: ' + actual_output, file=sys.stderr)
            assert re.compile(expected_regex, re.S).search(actual_output)
    finally:
        sys.stdin = stdin
        sys.stdout = stdout


@pytest.mark.parametrize('locale',
                         [
                             None,
                             ('ja'),
                             ('en'),
                             ('es'),
                             ('fr'),
                         ]
                         )
def test_remaining_translations_with_interpolations(
        locale: Optional[str]) -> None:
    if locale is None:
        unset_locale()
    else:
        assert isinstance(locale, str)  # for mypy
        set_locale(locale)
    # This will explode if they have a typo in the
    # interpolated variables in the translation.
    _('{vocab_file}-failed-to-read-{e}').format(vocab_file='bogus.csv', e=Exception())
    _('{vocab_file}-failed-to-write-{e}').format(vocab_file='bogus.csv', e=Exception())
