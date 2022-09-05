#!/usr/bin/python
import re
import readline
import sys
from colors import color  # type: ignore
from commands import CommandStack
from localisation import _, set_locale
from operations import format_help, get_operations
from vocab import Vocab
from typing import Final, List, Optional, Tuple


def main() -> None:
    set_locale('ja')
    print(color(_('nevs-japanese-vocab-list'), style='bold'))

    vocab_file: Final = 'vocab.csv'
    try:
        print(_('loading') + '...')
        vocab = Vocab(vocab_file)
    except Exception as e:
        print(_('{vocab_file}-failed-to-read-{e}').format(vocab_file=vocab_file, e=e))
        sys.exit(1)

    command_stack = CommandStack()
    print(format_help())

    search: Optional[str] = ''
    kanji_found: list[str] = []
    while True:
        (search, kanji_found) = main_stuff(
            vocab, command_stack, search, kanji_found)
        if search is None:
            break
    try:
        print(_('saving') + '...')
        vocab.save()
    except Exception as e:
        print(
            _('{vocab_file}-failed-to-write-{e}').format(vocab_file=vocab_file, e=e))
        sys.exit(1)


# Driven by tests.
def main_stuff(vocab: Vocab,
               command_stack: CommandStack,
               previous_search: Optional[str],
               previous_kanji_found: list[str]) -> tuple[Optional[str],
                                                         list[str]]:
    search = ''.join([c if c.isalnum() else ' ' for c in input(
        _('search') + ': ') if c.isalnum() or c.isspace()]).strip()
    params = [param for param in search.split(' ') if len(param) > 0]
    exact = False
    if len(params) == 0:
        search = '' if previous_search is None else previous_search
    else:
        command = params[0] if len(params) > 0 else ''
        params = params[1:] if len(params) > 1 else []
        if command == 'q' and len(params) == 0:
            return None, []
        else:
            operations = get_operations()
            if command in operations:
                operation_descriptor = operations[command]
                params = replace_indices(
                    vocab,
                    previous_search,
                    previous_kanji_found,
                    params,
                    operation_descriptor.accepts_english_params)
                if len(params) == operation_descriptor.expected_params and (
                        operation_descriptor.validation is None or operation_descriptor.validation(command_stack)):
                    result = operation_descriptor.operation(
                        command_stack, vocab, params)

                    if result.message is not None:
                        print(result.message)
                    if result.invalidate_previous_results:
                        previous_kanji_found = []
                    if result.new_search is None:
                        search = '' if previous_search is None else previous_search
                        if not result.repeat_previous_search:
                            return search, previous_kanji_found
                    else:
                        search = result.new_search
                        exact = True
                else:
                    print(operation_descriptor.error_message)
                    search = '' if previous_search is None else previous_search
            elif len(params) > 0:
                print(_('usage-h-to-show-usage'))
                return previous_search, previous_kanji_found

    if search == '':
        return '', previous_kanji_found

    kanji_found = vocab.search(search, exact)
    if len(kanji_found) > 0:
        print(_('found') + f': ({len(kanji_found)})')
        for kanji_index, kanji in enumerate(kanji_found):
            out = [
                color(f'{kanji_index + 1:4d}', fg='grey') + ' ' +
                color(vocab.get_list_name(kanji), fg='grey') + ' ' + kanji
            ]
            kana_list = vocab.get_kana(kanji)
            if len(kana_list) > 0:
                out.append(
                    color(
                        ' '.join(
                            [
                                f'{color(str(kana_index + 1), fg="grey")} {kana}' for kana_index,
                                kana in enumerate(kana_list)]),
                        fg='grey'))
            if vocab.is_known(kanji):
                green_tick = color('✓', fg='green')
                out.append(green_tick)
            print('  ' + ' '.join(out))
    else:
        print(_('nothing-found'))
    return search, kanji_found


def replace_indices(
        vocab: Vocab,
        previous_search: Optional[str],
        kanji_found: list[str],
        params: list[str],
        accepts_english_params: bool) -> list[str]:
    """ Given a set of search results, and command
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
            if (kanji_index == -1
                    and previous_search is not None
                    and len(previous_search) > 0):
                params[0] = previous_search
            elif kanji_index >= 0 and kanji_index < len(kanji_found):
                kanji = kanji_found[kanji_index]
                params[0] = kanji
    if (kanji is not None
            and len(params) > 1
            and __is_index(params[1])):
        kana = vocab.get_kana(kanji)
        kana_index = int(params[1]) - 1
        if kana_index >= 0 and kana_index < len(kana):
            params[1] = kana[kana_index]
    params = [
        param for param in params
        if accepts_english_params and not __is_index(param) or
        __is_kanji_or_kana(param)
    ]
    return params


def __is_index(s: str) -> bool:
    # Because isnumeric doesn't know about negative numbers.
    return re.match('^[-+]?[0-9]+$', s) is not None


def __is_kanji_or_kana(s: str) -> bool:
    return re.match(
        '^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FBF]+$',
        s) is not None


if __name__ == '__main__':
    main()
    sys.exit(0)
