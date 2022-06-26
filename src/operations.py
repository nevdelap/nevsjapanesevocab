from colors import color
from jamdict import Jamdict
from src.commands import *
from typing import Optional, Tuple

"""

Operations return:

- optional message to display,
- an optional string to search for, otherwise repeat the previous search,
- whether to repeat the previous search,
- whether to invalidate the previous search results.

"""


jam = Jamdict()


def look_up(command_stack: CommandStack, vocab: str, params: [
            str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 1
    search = params[0]
    result = jam.lookup(search)
    if len(result.entries) > 0:
        for entry in result.entries:
            print('  ' + entry.text(True))
    else:
        print('何も見つからない。')
    return (None, None, False, False)


def add(command_stack: CommandStack, vocab: str, params: [
        str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 1
    kanji = params[0]
    if vocab.contains(kanji):
        print(f'{kanji}は既に有る。')
    else:
        command_stack.do(AddCommand(vocab, kanji))
    return (None, kanji, False, False)


def change(command_stack: CommandStack, vocab: str, params: [
           str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 2
    kanji, new_kanji = params[:2]
    search = None
    invalidate_previous_search_results = False
    if not vocab.contains(kanji):
        print(f'{kanji}は見つからない。')
    elif vocab.contains(new_kanji):
        print(f'{new_kanji}は既に有る。')
        search = new_kanji
    else:
        command_stack.do(ChangeCommand(vocab, kanji, new_kanji))
        search = new_kanji
        invalidate_previous_search_results = True
    return (None, search, False, invalidate_previous_search_results)


def delete(command_stack: CommandStack, vocab: str, params: [
           str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 1
    kanji = params[0]
    invalidate_previous_search_results = False
    if not vocab.contains(kanji):
        print(f'{kanji}は見つからない。')
    else:
        command_stack.do(DeleteCommand(vocab, kanji))
        print(f'{kanji}は削除した。')
        invalidate_previous_search_results = True
    return (None, None, False, invalidate_previous_search_results)


def add_kana(command_stack: CommandStack, vocab: str, params: [
             str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 2
    kanji, kana = params[:2]
    if vocab.contains(kanji, kana):
        print(f'{kanji}は{kana}が既に有る。')
    else:
        command_stack.do(AddKanaCommand(vocab, kanji, kana))
    return (None, kanji, False, False)


def change_kana(
    command_stack: CommandStack,
    vocab: str,
    params: [str]
) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 3
    kanji, kana, new_kana = params[:3]
    search = None
    if not vocab.contains(kanji):
        print(f'{kanji}は見つからない。')
    elif not vocab.contains(kanji, kana):
        print(f'{kanji}は{kana}が見つからない。')
    else:
        search = kanji
        if vocab.contains(kanji, new_kana):
            print(f'{kanji}は{new_kana}が既に有る。')
        else:
            command_stack.do(ChangeKanaCommand(vocab, kanji, kana, new_kana))
    return (None, search, False, False)


def delete_kana(
    command_stack: CommandStack,
    vocab: str,
    params: [str]
) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 2
    kanji, kana = params[:2]
    invalidate_previous_search_results = False
    if not vocab.contains(kanji, kana):
        print(f'{kanji}は{kana}が見つからない。')
    else:
        command_stack.do(DeleteKanaCommand(vocab, kanji, kana))
        print(f'{kanji}は{kana}が削除した。')
        invalidate_previous_search_results = True
    return (None, None, False, invalidate_previous_search_results)


def toggle_known_status(command_stack: CommandStack, vocab: str, params: [
                        str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 1
    kanji = params[0]
    search = None
    if not vocab.contains(kanji):
        print(f'{kanji}は見つからない。')
    else:
        command_stack.do(ToggleKnownCommand(vocab, kanji))
        search = kanji
    return (None, kanji, False, False)


def undo(command_stack: CommandStack, vocab: str, params: [
         str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 0
    message = command_stack.undo()
    return (message, None, False, True)


def redo(command_stack: CommandStack, vocab: str, params: [
         str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 0
    message = command_stack.redo()
    return (message, None, False, True)


def save(command_stack: CommandStack, vocab: str, params: [
         str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 0
    try:
        print('書き込み中...')
        vocab.save()
    except Exception as e:
        print(f'{vocab_file}が書き込みに失敗した。☹ {e}')
        sys.exit(1)
    return (None, None, False, False)


def stats(command_stack: CommandStack, vocab: str, params: [
          str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    assert len(params) == 0
    print('データ:\n  分かった: %d\n  学んでいる %d\n  合計: %d\n' % vocab.get_stats())
    return (None, None, False, False)


__operation_help = [
    (None, '<漢字|仮名>', '検索', 2),
    ('l', '<漢字|仮名>', '辞書検索', 2),
    ('a', '<漢字>', '新漢字', 3),
    ('d', '<漢字>', '漢字削除', 3),
    ('c', '<現在の漢字> <漢字>', '漢字変更', 1),
    ('ak', '<漢字> <仮名>', '新仮名', 2),
    ('dk', '<漢字> <仮名>', '仮名削除', 2),
    ('ck', '<現在の仮名> <仮名>', '仮名変更', 1),
    ('t', '<漢字>', '分かったか(%s)否か\n\t\t\t\t  を切り換える。' % color('✓', fg='green'), 3),
    ('u', None, '元に戻す。', 4),
    ('r', None, '遣り直す。', 4),
    ('s', None, '書き込む。', 4),
    ('k', None, 'データ', 4),
    ('h', None, 'この使い方を表示する。', 4),
    ('q', None, '終了', 4),
]


def show_help(command_stack: CommandStack, vocab: str, params: [
              str]) -> Optional[Tuple[str, Optional[str], bool, bool]]:
    print('\n  使い方:\n')
    for (command, params, help_text, tabs) in __operation_help:
        out = []
        if command is not None:
            out.append(color(command, style='bold'))
        if params is not None:
            out.append(color(params, style='bold'))
        out.append('\t' * tabs + help_text)
        print('    ' + ' '.join(out))
    print()
    return (None, None, False, False)


__operations = {
    'l': (1, None, '使い方: l <漢字|仮名>', look_up),
    'a': (1, None, '使い方: a <漢字>', add),
    'd': (1, None, '使い方: d <漢字>', delete),
    'c': (2, None, '使い方: c <現在の漢字> <漢字>', change),
    'ak': (2, None, '使い方: a <漢字> <仮名>', add_kana),
    'dk': (2, None, '使い方: d <漢字> <仮名>', delete_kana),
    'ck': (3, None, '使い方: c <漢字> <現在の仮名> <仮名>', change_kana),
    't': (1, None, '使い方: t <漢字>', toggle_known_status),
    'u': (0, lambda command_stack: command_stack.undoable(), '元に戻すものがない。', undo),
    'r': (0, lambda command_stack: command_stack.redoable(), '遣り直しものがない。', redo),
    's': (0, None, None, save),
    'k': (0, None, None, stats),
    'h': (0, None, None, show_help)
}

assert sorted([operation[0] for operation in __operation_help if operation[0] not in [
              None, 'q']]) == sorted(list(__operations))


def get_operations():
    return __operations
