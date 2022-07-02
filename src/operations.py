import sys
from colors import color  # type: ignore
from commands import *
from jamdict import Jamdict  # type: ignore
from localisation import _, set_locale
from typing import Callable, Dict, Final, List, Optional, Tuple
from vocab import Vocab

# A function that can be called to check if the operation is
# possible given the current state of things.
OperationPrecheck = Callable[[CommandStack], bool]

OperationResult = Tuple[
    Optional[str],  # a message to display.
    # a string to search for, otherwise repeat the previous search,
    Optional[str],
    bool,  # or whether to repeat the previous search.
    bool,  # whether to invalidate the previous search results.
]

# Signature of the method function an operation.
Operation = Callable[[CommandStack, Vocab, List[str]], OperationResult]

# Definition of an operation.
OperationDescriptor = Tuple[
    int,  # number of params.
    Optional[OperationPrecheck],
    Optional[str],  # params.
    Operation
]


jam: Final = Jamdict()


def __look_up(command_stack: CommandStack, vocab: Vocab,
              params: List[str]) -> OperationResult:
    assert len(params) == 1
    search = params[0]
    result = jam.lookup(search)
    if len(result.entries) > 0:
        for entry in result.entries:
            print('  ' + entry.text(True))
    else:
        print('何も見つからない。')
    return (None, None, False, False)


def __add(command_stack: CommandStack, vocab: Vocab,
          params: List[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    if kanji in vocab:
        print(f'{kanji}は既に有る。')
    else:
        command_stack.do(AddCommand(vocab, kanji))
    return (None, kanji, False, False)


def __change(command_stack: CommandStack, vocab: Vocab,
             params: List[str]) -> OperationResult:
    assert len(params) == 2
    kanji, new_kanji = params[:2]
    search = None
    invalidate_previous_search_results = False
    if kanji not in vocab:
        print(f'{kanji}は見つからない。')
    elif new_kanji in vocab:
        print(f'{new_kanji}は既に有る。')
        search = new_kanji
    else:
        command_stack.do(ChangeCommand(vocab, kanji, new_kanji))
        search = new_kanji
        invalidate_previous_search_results = True
    return (None, search, False, invalidate_previous_search_results)


def __delete(command_stack: CommandStack, vocab: Vocab,
             params: List[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    invalidate_previous_search_results = False
    if kanji not in vocab:
        print(f'{kanji}は見つからない。')
    else:
        command_stack.do(DeleteCommand(vocab, kanji))
        print(f'{kanji}は削除した。')
        invalidate_previous_search_results = True
    return (None, None, False, invalidate_previous_search_results)


def __add_kana(command_stack: CommandStack, vocab: Vocab,
               params: List[str]) -> OperationResult:
    assert len(params) == 2
    kanji, kana = params[:2]
    if vocab.contains(kanji, kana):
        print(f'{kanji}は{kana}が既に有る。')
    else:
        command_stack.do(AddKanaCommand(vocab, kanji, kana))
    return (None, kanji, False, False)


def __change_kana(command_stack: CommandStack, vocab: Vocab,
                  params: List[str]) -> OperationResult:
    assert len(params) == 3
    kanji, kana, new_kana = params[:3]
    search = None
    if kanji not in vocab:
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


def __delete_kana(command_stack: CommandStack, vocab: Vocab,
                  params: List[str]) -> OperationResult:
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


def __toggle_known_status(
        command_stack: CommandStack,
        vocab: Vocab,
        params: List[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    search = None
    if kanji not in vocab:
        print(f'{kanji}は見つからない。')
    else:
        command_stack.do(ToggleKnownCommand(vocab, kanji))
        search = kanji
    return (None, kanji, False, False)


def __undo(command_stack: CommandStack, vocab: Vocab,
           params: List[str]) -> OperationResult:
    assert len(params) == 0
    message = command_stack.undo()
    return (message, None, False, True)


def __redo(command_stack: CommandStack, vocab: Vocab,
           params: List[str]) -> OperationResult:
    assert len(params) == 0
    message = command_stack.redo()
    return (message, None, False, True)


def __save(command_stack: CommandStack, vocab: Vocab,
           params: List[str]) -> OperationResult:
    assert len(params) == 0
    try:
        print(_('saving') + '...')
        vocab.save()
    except Exception as e:
        print(_('{vocab_file}-failed-to-write-{e}').format(vocab_file=vocab.filename, e=e))
        sys.exit(1)
    return (None, None, False, False)


def __stats(command_stack: CommandStack, vocab: Vocab,
            params: List[str]) -> OperationResult:
    assert len(params) == 0
    (known, learning) = vocab.get_stats()
    print(
        f'データ:\n  分かった: {known}\n  学んでいる {learning}\n  合計: {known + learning}\n')
    return (None, None, False, False)


def __english(command_stack: CommandStack, vocab: Vocab,
              params: List[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('en')
    return (None, None, False, False)


def __french(command_stack: CommandStack, vocab: Vocab,
             params: List[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('fr')
    return (None, None, False, False)


def __japanese(command_stack: CommandStack, vocab: Vocab,
               params: List[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('ja')
    return (None, None, False, False)


def __spanish(command_stack: CommandStack, vocab: Vocab,
              params: List[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('es')
    return (None, None, False, False)


OperationHelp = List[
    Tuple[
        Optional[str],  # command.
        Optional[str],  # parameters.
        str,  # help text.
        int, int  # tabs and spaces to help layout.
    ]
]

__green_tick = color('✓', fg='green')

__operation_help: OperationHelp = [
    (None, '<漢字|仮名>', '検索', 2, 2),
    ('l', '<漢字|仮名>', '辞書検索', 2, 2),
    ('a', '<漢字>', '新漢字', 3, 2),
    ('d', '<漢字>', '漢字削除', 3, 2),
    ('c', '<現在の漢字> <漢字>', '漢字変更', 1, 2),
    ('ak', '<漢字> <仮名>', '新仮名', 2, 2),
    ('dk', '<漢字> <仮名>', '仮名削除', 2, 2),
    ('ck', '<漢字> <現在の仮名> <仮名>', '仮名変更', 0, 0),
    ('t', f'<漢字>', '分かったか({green_tick})\n\t\t\t\t  否かを\n\t\t\t\t  切り換える。', 3, 2),
    ('u', None, '元に戻す。', 4, 2),
    ('r', None, '遣り直す。', 4, 2),
    ('s', None, '書き込む。', 4, 2),
    ('k', None, 'データ', 4, 2),
    ('en', None, 'English', 4, 2),
    ('es', None, 'español', 4, 2),
    ('fr', None, 'français', 4, 2),
    ('ja', None, '日本語', 4, 2),
    ('h', None, 'この使い方\n\t\t\t\t  を表示する。', 4, 2),
    ('q', None, '終了', 4, 2),
]


def __show_help(command_stack: CommandStack, vocab: Vocab,
                params_unused: List[str]) -> OperationResult:
    show_help()
    return (None, None, False, False)


def show_help() -> None:
    print('\n  使い方:\n')
    for (command, params, help_text, tabs, spaces) in __operation_help:
        out = []
        if command is not None:
            out.append(color(command, style='bold'))
        if params is not None:
            out.append(color(params, style='bold'))
        out.append('\t' * tabs + ' ' * spaces + help_text)
        print('    ' + ' '.join(out))
    print()


OperationsDescriptors = Dict[
    str,  # command.
    OperationDescriptor
]

__operations: OperationsDescriptors = {
    'l': (1, None, '使い方: l <漢字|仮名>', __look_up),
    'a': (1, None, '使い方: a <漢字>', __add),
    'd': (1, None, '使い方: d <漢字>', __delete),
    'c': (2, None, '使い方: c <現在の漢字> <漢字>', __change),
    'ak': (2, None, '使い方: a <漢字> <仮名>', __add_kana),
    'dk': (2, None, '使い方: d <漢字> <仮名>', __delete_kana),
    'ck': (3, None, '使い方: c <漢字> <現在の仮名> <仮名>', __change_kana),
    't': (1, None, '使い方: t <漢字>', __toggle_known_status),
    'u': (0, lambda command_stack: command_stack.undoable(), '元に戻すものがない。', __undo),
    'r': (0, lambda command_stack: command_stack.redoable(), '遣り直しものがない。', __redo),
    's': (0, None, None, __save),
    'k': (0, None, None, __stats),
    'en': (0, None, 'English', __english),
    'es': (0, None, 'español', __spanish),
    'fr': (0, None, 'français', __french),
    'ja': (0, None, '日本語', __japanese),
    'h': (0, None, None, __show_help),
}

assert sorted([str(operation[0]) for operation in __operation_help if operation[0] not in [
              None, 'q']]) == sorted(list(__operations))


def get_operations() -> OperationsDescriptors:
    return __operations
