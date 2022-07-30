import sys
from colors import color  # type: ignore
from commands import *
from jamdict import Jamdict  # type: ignore
from localisation import _, get_locale, set_locale
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

OperationHelp = Tuple[
    str,  # command.
    str,  # parameters.
    str,  # help text.
]

OperationsHelp = List[OperationHelp]

# Signature of the method function an operation.
Operation = Callable[
    [CommandStack, Vocab, List[str]],
    OperationResult
]

# Definition of an operation.
OperationDescriptor = Tuple[
    int,  # number of params.
    bool, # accepts English params.
    Optional[OperationPrecheck],
    Optional[str],  # params.
    Operation
]

OperationsDescriptors = Dict[
    str,  # command.
    OperationDescriptor
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
        print(_('nothing-found'))
    return (None, None, False, False)


def __add(command_stack: CommandStack, vocab: Vocab,
          params: List[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    if kanji in vocab:
        print(_('{kanji}-already-exists').format(kanji=kanji))
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
        print(_('{kanji}-not-found').format(kanji=kanji))
    elif new_kanji in vocab:
        print(_('{kanji}-already-exists').format(kanji=new_kanji))
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
        print(_('{kanji}-not-found').format(kanji=kanji))
    else:
        command_stack.do(DeleteCommand(vocab, kanji))
        print(_('{kanji}-deleted').format(kanji=kanji))
        invalidate_previous_search_results = True
    return (None, None, False, invalidate_previous_search_results)


def __add_kana(command_stack: CommandStack, vocab: Vocab,
               params: List[str]) -> OperationResult:
    assert len(params) == 2
    kanji, kana = params[:2]
    if vocab.contains(kanji, kana):
        print(_('{kana}-already-exists-for-{kanji}').format(kanji=kanji, kana=kana))
    else:
        command_stack.do(AddKanaCommand(vocab, kanji, kana))
    return (None, kanji, False, False)


def __change_kana(command_stack: CommandStack, vocab: Vocab,
                  params: List[str]) -> OperationResult:
    assert len(params) == 3
    kanji, kana, new_kana = params[:3]
    search = None
    if kanji not in vocab:
        print(_('{kanji}-not-found').format(kanji=kanji))  # Needs test.
    elif not vocab.contains(kanji, kana):
        print(_('{kana}-not-found-for-{kanji}').format(kanji=kanji, kana=kana))
    else:
        search = kanji
        if vocab.contains(kanji, new_kana):
            print(
                _('{kana}-already-exists-for-{kanji}').format(kanji=kanji, kana=new_kana))
        else:
            command_stack.do(ChangeKanaCommand(vocab, kanji, kana, new_kana))
    return (None, search, False, False)


def __delete_kana(command_stack: CommandStack, vocab: Vocab,
                  params: List[str]) -> OperationResult:
    assert len(params) == 2
    kanji, kana = params[:2]
    invalidate_previous_search_results = False
    if not vocab.contains(kanji, kana):
        print(_('{kana}-not-found-for-{kanji}').format(kanji=kanji, kana=kana))
    else:
        command_stack.do(DeleteKanaCommand(vocab, kanji, kana))
        print(_('{kana}-deleted-from-{kanji}').format(kanji=kanji, kana=kana))
        invalidate_previous_search_results = True
    return (None, kanji, False, invalidate_previous_search_results)


def __toggle_known_status(
        command_stack: CommandStack,
        vocab: Vocab,
        params: List[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    search = None
    if kanji not in vocab:
        print(_('{kanji}-not-found').format(kanji=kanji))
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
        print(
            _('{vocab_file}-failed-to-write-{e}').format(vocab_file=vocab.filename, e=e))
        sys.exit(1)
    return (None, None, False, False)


def __info(command_stack: CommandStack, vocab: Vocab,
           params: List[str]) -> OperationResult:
    assert len(params) == 0
    (known, learning) = vocab.get_info()
    print('\n'
          + _('info') + ':\n  '
          + _('known') + f': {known}\n  '
          + _('learning') + f': {learning}\n  '
          + _('total') + f': {known + learning}\n')
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


__green_tick = color('✓', fg='green')


def __operations_help() -> OperationsHelp:
    return [
        ('', _('kanji') + _('bar') + _('kana'), _('help-search')),
        ('l', _('kanji') + _('bar') + _('kana'), _('help-dictionary-search')),
        ('a', _('kanji'), _('help-new-kanji')),
        ('d', _('kanji'), _('help-delete-kanji')),
        ('c', _('kanji') + _('space') + _('new-kanji'), _('help-change-kanji')),
        ('ak', _('kanji') + _('space') + _('kana'), _('help-new-kana')),
        ('dk', _('kanji') + _('space') + _('kana'), _('help-delete-kana')),
        ('ck', _('kanji') + _('space') + _('kana') + _('space') + _('new-kana'), _('help-change-kana')),
        ('t', _('kanji'), _('help-known-or-not?{green_tick}').format(green_tick=__green_tick)),
        ('u', '', _('help-undo')),
        ('r', '', _('help-redo')),
        ('s', '', _('help-save')),
        ('i', '', _('help-info')),
        ('en', '', 'English'),
        ('es', '', 'español'),
        ('fr', '', 'français'),
        ('ja', '', '日本語'),
        ('h', '', _('help-show-this-help')),
        ('q', '', _('help-quit')),
    ]


def __show_help(command_stack: CommandStack, vocab: Vocab,
                params_unused: List[str]) -> OperationResult:
    print(format_help())
    return (None, None, False, False)


def format_help() -> str:
    (bar, space) = ('\uFF5C', '\u3000') if get_locale() == 'ja' else ('|', ' ')
    help = '\n' + _('usage') + ':\n'
    (command_width, params_width, help_text_width) = __get_help_column_widths()
    for (command, params, help_text) in __operations_help():
        help += ('  '
                 + command.ljust(command_width) + ' '
                 + params.ljust(params_width, space) + space
                 + help_text + '\n')
    return help


def __get_help_column_widths() -> Tuple[int, int, int]:
    widths = (0, 0, 0)
    for (command, params, help_text) in __operations_help():
        widths = (
            widths[0] if widths[0] >= len(command) else len(command),
            widths[1] if widths[1] >= len(params) else len(params),
            widths[2] if widths[2] >= len(help_text) else len(help_text),
        )
    return widths


def __operations() -> OperationsDescriptors:
    return {
        'l': (
            1,
            True,
            None,
            _('usage') + ': l ' + _('kanji') + _('bar') + _('kana'),
            __look_up),
        'a': (
            1,
            False,
            None,
            _('usage') + ': a ' + _('kanji'),
            __add),
        'd': (
            1,
            False,
            None,
            _('usage') + ': d ' + _('kanji'),
            __delete),
        'c': (
            2,
            False,
            None,
            _('usage') + ': c ' + _('kanji') + _('space') + _('new-kanji'),
            __change),
        'ak': (
            2,
            False,
            None,
            _('usage') + ': a ' + _('kanji') + _('space') + _('kana'),
            __add_kana),
        'dk': (
            2,
            False,
            None,
            _('usage') + ': d ' + _('kanji') + _('space') + _('kana'),
            __delete_kana),
        'ck': (
            3,
            False,
            None,
            _('usage') + ': c ' + _('kanji') + _('space') + _('kana') + _('space') + _('new-kana'),
            __change_kana),
        't': (
            1,
            False,
            None,
            _('usage') + ': t ' + _('kanji'),
            __toggle_known_status),
        'u': (
            0,
            False,
            lambda command_stack: command_stack.undoable(),
            _('there-is-nothing-to-undo'),
            __undo),
        'r': (
            0,
            False,
            lambda command_stack: command_stack.redoable(),
            _('there-is-nothing-to-redo'),
            __redo),
        's': (
            0,
            False,
            None,
            None,
            __save),
        'i': (
            0,
            False,
            None,
            None,
            __info),
        'en': (
            0,
            False,
            None,
            'English',
            __english),
        'es': (
            0,
            False,
            None,
            'español',
            __spanish),
        'fr': (
            0,
            False,
            None,
            'français',
            __french),
        'ja': (
            0,
            False,
            None,
            '日本語',
            __japanese),
        'h': (
            0,
            False,
            None,
            None,
            __show_help),
    }


assert sorted([operation[0] for operation in __operations_help()
               if operation[0] not in ['', 'q']]) == sorted(list(__operations()))


def get_operations() -> OperationsDescriptors:
    return __operations()
