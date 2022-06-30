#!/usr/bin/python
import readline
import shlex
import sys
from colors import color  # type: ignore
from commands import CommandStack
from operations import get_operations
from vocab import Vocab
from typing import Final, List, Optional, Tuple


def main() -> None:
    print(color('ネフの日本語語彙リスト', style='bold'))

    vocab_file: Final = 'vocab.csv'
    try:
        print('読み込み中...')
        vocab = Vocab(vocab_file)
    except Exception as e:
        print(f'{vocab_file}が読み込みに失敗した。, ☹ {e}')
        sys.exit(1)

    command_stack = CommandStack()

    print('hを押してヘルプを表示する。')
    search: Optional[str] = ''
    kanji_found: List[str] = []
    while True:
        (search, kanji_found) = main_stuff(
            vocab, command_stack, search, kanji_found)
        if search is None:
            break
    try:
        print('書き込み中...')
        vocab.save()
    except Exception as e:
        print(f'{vocab_file}が書き込みに失敗した。☹ {e}')
        sys.exit(1)

# Driven by tests.


def main_stuff(vocab: Vocab,
               command_stack: CommandStack,
               previous_search: Optional[str],
               previous_kanji_found: List[str]) -> Tuple[Optional[str],
                                                         List[str]]:
    search = input('検索: ').strip()
    params = shlex.split(search)
    exact = False
    if len(params) == 0:
        search = '' if previous_search is None else previous_search
    else:
        params = replace_indices(
            vocab,
            previous_search,
            previous_kanji_found,
            params)
        command = params[0] if len(params) > 0 else ''
        params = params[1:] if len(params) > 1 else []
        if command == 'q' and len(params) == 0:
            return None, []
        else:
            operations = get_operations()
            if command in operations:
                (expected_params, validation, error_message,
                    operation) = operations[command]
                if len(params) == expected_params and (
                        validation is None or validation(command_stack)):
                    (
                        message,
                        new_search,
                        repeat_previous_search,
                        invalidate_previous_search
                    ) = operation(
                        command_stack,
                        vocab,
                        params
                    )
                    if message is not None:
                        print(message)
                    if invalidate_previous_search:
                        previous_kanji_found = []
                    if new_search is None:
                        search = '' if previous_search is None else previous_search
                        if not repeat_previous_search:
                            return search, previous_kanji_found
                    else:
                        search = new_search
                        exact = True
                else:
                    print(error_message)
            elif len(params) > 0:
                print('使い方: h 使い方を表示する。')
                return previous_search, previous_kanji_found

    if search == '':
        return '', previous_kanji_found

    kanji_found = vocab.search(search, exact)
    if len(kanji_found) > 0:
        print('見つかった: (%d)' % len(kanji_found))
        for kanji_index, kanji in enumerate(kanji_found):
            out = [
                '%s %s %s' % (
                    color('%4d' % (kanji_index + 1), fg='grey'),
                    color(vocab.get_list_name(kanji), fg='grey'),
                    kanji)
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
            if vocab.get_known(kanji):
                out.append(color('✓', fg='green'))
            print('  ' + ' '.join(out))
    else:
        print('何も見つからない。')
    return search, kanji_found


def replace_indices(
        vocab: Vocab,
        previous_search: Optional[str],
        kanji_found: list[str],
        params: list[str]) -> list[str]:
    """ Given a set of search results, and command
    parameters that reference kanji and kana by index in
    those results, replace the indices with the kanji and
    kana."""
    assert all(Vocab.valid_string(kanji) for kanji in kanji_found)
    assert all(vocab.contains(kanji) for kanji in kanji_found)
    assert all(len(p) > 0 for p in params)
    if len(params) > 1 and params[1].isnumeric():
        kanji_index = int(params[1]) - 1
        if kanji_index == -1 \
                and previous_search is not None and len(previous_search) > 0:
            params[1] = previous_search
        elif kanji_index >= 0 and kanji_index < len(kanji_found):
            kanji = kanji_found[kanji_index]
            params[1] = kanji
            if len(params) > 2 and params[2].isnumeric():
                kana = vocab.get_kana(kanji)
                kana_index = int(params[2]) - 1
                if kana_index >= 0 and kana_index < len(kana):
                    params[2] = kana[kana_index]
    return params


if __name__ == '__main__':
    main()
    sys.exit(0)
