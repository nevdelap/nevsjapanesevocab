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
    vocab.add('new')
    vocab.add('new2')
    vocab.add('new3')
    vocab.add_kana('new2', 'kana1')
    vocab.add_kana('new2', 'kana2')
    vocab.add_kana('new2', 'kana3')
    return vocab


@pytest.mark.parametrize('previous_search, params, expected_result',
                         [
                             ('new', ['n', '-50'], ['n']),
                             ('new', ['n', '-1'], ['n']),
                             ('new', ['n', '0'], ['n']),
                             ('new', ['n', '1'], ['n', 'new']),
                             ('new', ['n', '2'], ['n', 'new2']),
                             ('new', ['n', '3'], ['n', 'new3']),
                             ('new', ['n', '4'], ['n']),
                             ('new', ['n', '999'], ['n']),
                             ('new', ['n', '1', '1'], ['n', 'new']),
                             ('new', ['n', 'new', '1'], ['n', 'new']),
                             ('new', ['n', '2', '-50'], ['n', 'new2']),
                             ('new', ['n', '2', '-1'], ['n', 'new2']),
                             ('new', ['n', '2', '0'], ['n', 'new2']),
                             ('new', ['n', '2', '1'], ['n', 'new2', 'kana1']),
                             ('new', ['n', '2', '2'], ['n', 'new2', 'kana2']),
                             ('new', ['n', '2', '3'], ['n', 'new2', 'kana3']),
                             ('new', ['n', '2', '4'], ['n', 'new2']),
                             ('new', ['n', '2', '999'], ['n', 'new2']),
                             ('new', ['n', 'new2', '-50'], ['n', 'new2']),
                             ('new', ['n', 'new2', '-1'], ['n', 'new2']),
                             ('new', ['n', 'new2', '0'], ['n', 'new2']),
                             ('new', ['n', 'new2', '1'], ['n', 'new2', 'kana1']),
                             ('new', ['n', 'new2', '2'], ['n', 'new2', 'kana2']),
                             ('new', ['n', 'new2', '3'], ['n', 'new2', 'kana3']),
                             ('new', ['n', 'new2', '4'], ['n', 'new2']),
                             ('new', ['n', 'new2', '999'], ['n', 'new2']),
                         ]
                         )
def test_replace_indices(
        vocab: Vocab,
        previous_search: str,
        params: List[str],
        expected_result: List[str]) -> None:
    found_kanji = vocab.search(previous_search)
    assert replace_indices(vocab, '', found_kanji, params) == expected_result

# This has examples of all translations to ensure that the
# translations themselves are syntactically correct in
# regards to interpolation. E.g. {new_kanji}, not
# {new-kanji}.


def __io() -> List[Tuple[str, str]]:
    return [
        ('\n', _('search')),
        # Bad command.
        ('w w w', _('usage-h-to-show-usage')),
        # Bad usage.
        ('t', f'{_("usage")}: t {_("kanji")}'),
        # Search found and not found.
        ('研究', f'{_("found")}: \\(1\\)\n     1 0100 研究 1 けんきゅう'),
        ('notfound', _('nothing-found')),
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
        ('new', _('nothing-found')),
        ('a new', f'{_("found")}: \\(1\\)\n     1 0100 new'),
        ('new', f'{_("found")}:.*1 0100 new'),
        ('c new NEW', f'{_("found")}: \\(1\\)\n     1 0100 NEW'),
        ('NEW', f'{_("found")}: \\(1\\)\n     1 0100 NEW'),
        ('u',
         _('{new_kanji}-changed-back-to-{kanji}').format(kanji='new',
                                                         new_kanji='NEW')),
        ('r', _('{kanji}-changed-to-{new_kanji}').format(kanji='new', new_kanji='NEW')),
        ('u',
         _('{new_kanji}-changed-back-to-{kanji}').format(kanji='new',
                                                         new_kanji='NEW')),
        ('u',
         _('{kanji}-has-been-deleted-from-list-{list_name}').format(kanji='new',
                                                                    list_name='0100')),
        ('r',
         _('{kanji}-added-to-list-{list_name}').format(kanji='new',
                                                       list_name='0100')),
        ('d new', _('{kanji}-deleted').format(kanji='new')),
        ('u',
         _('{kanji}-added-to-list-{list_name}').format(kanji='new',
                                                       list_name='0100')),
        ('r',
         _('{kanji}-has-been-deleted-from-list-{list_name}').format(kanji='new',
                                                                    list_name='0100')),
        ('u',
         _('{kanji}-added-to-list-{list_name}').format(kanji='new',
                                                       list_name='0100')),
        ('ak new kana', f'{_("found")}: \\(1\\).*1 0100 new 1 kana'),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana')),
        ('r', _('{kana}-added-to-{kanji}').format(kanji='new', kana='kana')),
        ('dk new kana', _(
            '{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='new', kana='kana')),
        ('r', _('{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='new', kana='kana')),
        ('i', f'{_("info")}:\n  {_("known")}: 0\n  {_("learning")}: 6\n  {_("total")}: 6'),
        ('t new', f'{_("found")}: \\(1\\)\n     1 0100 new 1 kana ✓'),
        ('i', f'{_("info")}:\n  {_("known")}: 1\n  {_("learning")}: 5\n  {_("total")}: 6'),
        ('t new', f'{_("found")}: \\(1\\)\n     1 0100 new 1 kana[^✓]+$'),
        ('i', f'{_("info")}:\n  {_("known")}: 0\n  {_("learning")}: 6\n  {_("total")}: 6'),
        ('d new', _('{kanji}-deleted').format(kanji='new')),
        # Indexes.
        ('new', _('nothing-found')),
        ('a new', '1 0100 new'),
        ('ak 1 kana', '1 0100 new 1 kana'),
        ('ak 1 kana2', '1 0100 new 1 kana 2 kana2'),
        ('ak 1 kana3', '1 0100 new 1 kana 2 kana2 3 kana3'),
        ('ck 1 kana2 kana4', '1 0100 new 1 kana 2 kana4 3 kana3'),
        ('u',
         _('{new_kana}-changed-back-to-{kana}-for-{kanji}').format(kanji='new',
                                                                   kana='kana2',
                                                                   new_kana='kana4')),
        ('r',
         _('{kana}-changed-to-{new_kana}-for-{kanji}').format(kanji='new',
                                                              kana='kana2',
                                                              new_kana='kana4')),
        ('u',
         _('{new_kana}-changed-back-to-{kana}-for-{kanji}').format(kanji='new',
                                                                   kana='kana2',
                                                                   new_kana='kana4')),
        ('new', '1 0100 new 1 kana 2 kana2 3 kana3'),
        ('t 1', '1 0100 new 1 kana 2 kana2 3 kana3 ✓'),
        ('t 1', '1 0100 new 1 kana 2 kana2 3 kana3[^✓]+$'),
        ('dk 1 2',
         _('{kana}-deleted-from-{kanji}').format(kanji='new',
                                                 kana='kana2')),
        ('new', '1 0100 new 1 kana 2 kana3'),
        ('dk 1 2',
         _('{kana}-deleted-from-{kanji}').format(kanji='new',
                                                 kana='kana3')),
        ('new', '1 0100 new 1 kana'),
        ('dk 1 1', _(
            '{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana')),
        ('new', '1 0100 new'),
        ('c 1 NEW', f'{_("found")}: \\(1\\)\n     1 0100 NEW'),
        ('NEW', f'{_("found")}: \\(1\\)\n     1 0100 NEW'),
        ('u',
         _('{new_kanji}-changed-back-to-{kanji}').format(kanji='new',
                                                         new_kanji='NEW')),
        ('new', f'{_("found")}: \\(1\\)\n     1 0100 new'),
        ('d 1', _('{kanji}-deleted').format(kanji='new')),
        ('new', _('nothing-found')),
        ('u',
         _('{kanji}-added-to-list-{list_name}').format(kanji='new',
                                                       list_name='0100')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='new', kana='kana')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='new', kana='kana3')),
        ('u', _('{kana}-added-to-{kanji}').format(kanji='new', kana='kana2')),
        ('u',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='new',
                                                           known_status=_('already-known') + '\\(✓\\)')),
        ('u',
         _('toggled-the-{known_status}-of-{kanji}').format(kanji='new',
                                                           known_status=_('unknown'))),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana3')),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana2')),
        ('u', _('{kana}-deleted-from-{kanji}').format(kanji='new', kana='kana')),
        ('u',
         _('{kanji}-has-been-deleted-from-list-{list_name}').format(kanji='new',
                                                                    list_name='0100')),
        ('new', _('nothing-found')),
        # Each command's error messages.
        ('a new', f'{_("found")}: \\(1\\)\n     1 0100 new'),
        ('a new', _('{kanji}-already-exists').format(kanji='new')),
        ('c new2 new', _('{kanji}-not-found').format(kanji='new2')),
        ('c new new', _('{kanji}-already-exists').format(kanji='new')),
        ('d new2', _('{kanji}-not-found').format(kanji='new2')),
        ('ak new kana', f'{_("found")}: \\(1\\)\n     1 0100 new 1 kana'),
        ('ak new kana', _(
            '{kana}-already-exists-for-{kanji}').format(kanji='new', kana='kana')),
        ('ck new kana2 kana3', _(
            '{kana}-not-found-for-{kanji}').format(kanji='new', kana='kana2')),
        ('ck new kana kana', _(
            '{kana}-already-exists-for-{kanji}').format(kanji='new', kana='kana')),
        ('dk new kana2', _(
            '{kana}-not-found-for-{kanji}').format(kanji='new', kana='kana2')),
        ('t new2', _('{kanji}-not-found').format(kanji='new2')),
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
        kanji_found: List[str] = []
        for test_input, expected_regex in __io():
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
