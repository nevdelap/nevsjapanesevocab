import sys
import termios
import tty
from typing import Callable, Final, Sequence, NamedTuple, Optional

from colors import color  # type: ignore
from jamdict import Jamdict  # type: ignore

from commands import \
    AddCommand, AddKanaCommand, ChangeCommand, ChangeKanaCommand, \
    CommandStack, DeleteCommand, DeleteKanaCommand, ToggleKnownCommand
from localisation import _, get_locale, set_locale
from vocab import Vocab

# A function that can be called to check if the operation is
# possible given the current state of things.
OperationPrecheck = Callable[[CommandStack], bool]


class OperationResult(NamedTuple):
    message: Optional[str]
    # a string to search for, otherwise repeat the previous search,
    new_search: Optional[str]
    repeat_previous_search: bool
    invalidate_previous_results: bool


class OperationHelp(NamedTuple):
    command: str
    params: str
    help_text: str


OperationsHelp = list[OperationHelp]

# Signature of the method function an operation.
Operation = Callable[
    [CommandStack, Vocab, list[str]],
    OperationResult
]


class OperationDescriptor(NamedTuple):
    min_params: int
    max_params: Optional[int]
    accepts_english_params: bool
    validation: Optional[OperationPrecheck]
    error_message: Optional[str]
    operation: Operation

    def are_good_params(self, params: Sequence[str]) -> bool:
        return len(params) >= self.min_params and (
            self.max_params is None or len(params) <= self.max_params)

    def operation_is_valid(self, command_stack: CommandStack) -> bool:
        return self.validation is None or self.validation(command_stack)


OperationsDescriptors = dict[
    str,  # command.
    OperationDescriptor
]


class HelpColumnWidths(NamedTuple):
    command: int
    params: int
    help_text: int


# pylint: disable=invalid-name
jam: Final = Jamdict()


def __look_up(_command_stack: CommandStack, _vocab: Vocab,
              params: list[str]) -> OperationResult:
    assert len(params) >= 1
    search = ' '.join(params)
    result = jam.lookup(search)
    if len(result.entries) > 0:
        for entry in result.entries:
            print('  ' + entry.text(True))
    else:
        print(_('nothing-found'))
    return OperationResult(None, None, False, False)


def __add(command_stack: CommandStack, vocab: Vocab,
          params: list[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    if kanji in vocab:
        print(_('{kanji}-already-exists').format(kanji=kanji))
    else:
        command_stack.do(AddCommand(vocab, kanji))
    return OperationResult(None, kanji, False, False)


def __change(command_stack: CommandStack, vocab: Vocab,
             params: list[str]) -> OperationResult:
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
    return OperationResult(
        None,
        search,
        False,
        invalidate_previous_search_results)


def __delete(command_stack: CommandStack, vocab: Vocab,
             params: list[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    invalidate_previous_search_results = False
    if kanji not in vocab:
        print(_('{kanji}-not-found').format(kanji=kanji))
    else:
        command_stack.do(DeleteCommand(vocab, kanji))
        print(_('{kanji}-deleted').format(kanji=kanji))
        invalidate_previous_search_results = True
    return OperationResult(
        None,
        None,
        False,
        invalidate_previous_search_results)


def __add_kana(command_stack: CommandStack, vocab: Vocab,
               params: list[str]) -> OperationResult:
    assert len(params) == 2
    kanji, kana = params[:2]
    if vocab.contains(kanji, kana):
        print(_('{kana}-already-exists-for-{kanji}').format(kanji=kanji, kana=kana))
    else:
        command_stack.do(AddKanaCommand(vocab, kanji, kana))
    return OperationResult(None, kanji, False, False)


def __change_kana(command_stack: CommandStack, vocab: Vocab,
                  params: list[str]) -> OperationResult:
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
    return OperationResult(None, search, False, False)


def __delete_kana(command_stack: CommandStack, vocab: Vocab,
                  params: list[str]) -> OperationResult:
    assert len(params) == 2
    kanji, kana = params[:2]
    invalidate_previous_search_results = False
    if not vocab.contains(kanji, kana):
        print(_('{kana}-not-found-for-{kanji}').format(kanji=kanji, kana=kana))
    else:
        command_stack.do(DeleteKanaCommand(vocab, kanji, kana))
        print(_('{kana}-deleted-from-{kanji}').format(kanji=kanji, kana=kana))
        invalidate_previous_search_results = True
    return OperationResult(
        None,
        kanji,
        False,
        invalidate_previous_search_results)


def __toggle_known_status(
        command_stack: CommandStack,
        vocab: Vocab,
        params: list[str]) -> OperationResult:
    assert len(params) == 1
    kanji = params[0]
    if kanji not in vocab:
        print(_('{kanji}-not-found').format(kanji=kanji))
    else:
        command_stack.do(ToggleKnownCommand(vocab, kanji))
    return OperationResult(None, kanji, False, False)


__green_tick = color('✓', fg='green')


def __review(command_stack: CommandStack, vocab: Vocab,
             _params: list[str]) -> OperationResult:
    fd = sys.stdin.fileno()
    tcattr = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        kanjis = vocab.kanji
        # Operations done in review mode can be undone and
        # redone in review mode. Once out of review mode
        # operations done in review mode are just part of
        # the infinite undo stack.
        operations_count = 0
        kanji_index = 0
        # This stack allows reset the position in the list
        # of words being reviewed as undo's and redo's in the
        # context of review mode are done.
        stack: list[int] = []
        current = -1
        while kanji_index < len(kanjis):
            commands = ['y', 'n']
            if operations_count > 0:
                commands.append('u')
            if command_stack.redoable():
                commands.append('r')
            commands.append('q')
            prompt = ' 分かる(' + ', '.join(commands) + ')? '
            prompt_len = len(prompt) + 3  # todo, something about this 3
            erase = '\b' * prompt_len + ' ' * prompt_len + '\b' * prompt_len
            kanji = kanjis[kanji_index]
            if not vocab.is_known(kanji):
                print(f'  {kanji}{prompt}', end='')
                sys.stdout.flush()
                while True:
                    response = sys.stdin.read(1)
                    if response in commands:
                        break
                if response == 'q':
                    print('\r')
                    break
                if response in ['y', 'n']:
                    known = response == 'y'
                    if vocab.is_known(kanji) != known:
                        __toggle_known_status(command_stack, vocab, [kanji])
                        operations_count += 1
                        stack = stack[:current + 1]
                        stack.append(kanji_index)
                        current += 1
                    kanji_index += 1
                elif response == 'u':
                    __undo(command_stack, vocab, [])
                    operations_count -= 1
                    kanji_index = stack[current]
                    current -= 1
                elif response == 'r':
                    __redo(command_stack, vocab, [])
                    operations_count += 1
                    current += 1
                    kanji_index = stack[int(current)]
                print(f'{erase}', end='')
                if vocab.is_known(kanji):
                    print(f' {__green_tick}', end='')
                print('\r')
            else:
                kanji_index += 1
        assert operations_count >= current
        assert current < len(stack)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, tcattr)
    message = _(
        '{count}-kanji-changed-to-known').format(count=operations_count)
    return OperationResult(message, None, False, True)


def __undo(command_stack: CommandStack, _vocab: Vocab,
           params: list[str]) -> OperationResult:
    assert len(params) == 0
    message = command_stack.undo()
    return OperationResult(message, None, False, True)


def __redo(command_stack: CommandStack, _vocab: Vocab,
           params: list[str]) -> OperationResult:
    assert len(params) == 0
    message = command_stack.redo()
    return OperationResult(message, None, False, True)


def __save(_command_stack: CommandStack, vocab: Vocab,
           params: list[str]) -> OperationResult:
    assert len(params) == 0
    print(_('saving') + '...')
    vocab.save()
    return OperationResult(None, None, False, False)


def __info(_command_stack: CommandStack, vocab: Vocab,
           params: list[str]) -> OperationResult:
    assert len(params) == 0
    (known, learning) = vocab.get_info()
    print('\n'
          + _('info') + ':\n  '
          + _('known') + f': {known}\n  '
          + _('learning') + f': {learning}\n  '
          + _('total') + f': {known + learning}\n')
    return OperationResult(None, None, False, False)


def __english(_command_stack: CommandStack, _vocab: Vocab,
              params: list[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('en')
    return OperationResult(None, None, False, False)


def __french(_command_stack: CommandStack, _vocab: Vocab,
             params: list[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('fr')
    return OperationResult(None, None, False, False)


def __japanese(_command_stack: CommandStack, _vocab: Vocab,
               params: list[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('ja')
    return OperationResult(None, None, False, False)


def __spanish(_command_stack: CommandStack, _vocab: Vocab,
              params: list[str]) -> OperationResult:
    assert len(params) == 0
    set_locale('es')
    return OperationResult(None, None, False, False)


def __operations_help() -> OperationsHelp:
    return [
        OperationHelp('', _('kanji') + _('bar') + _('kana'), _('help-search')),
        OperationHelp('l', _('japanese') + _('bar') + _('english'), _('help-dictionary-search')),
        OperationHelp('a', _('kanji'), _('help-new-kanji')),
        OperationHelp('d', _('kanji'), _('help-delete-kanji')),
        OperationHelp('c', _('kanji') + _('space') + _('new-kanji'), _('help-change-kanji')),
        OperationHelp('ak', _('kanji') + _('space') + _('kana'), _('help-new-kana')),
        OperationHelp('dk', _('kanji') + _('space') + _('kana'), _('help-delete-kana')),
        OperationHelp('ck', _('kanji') + _('space') + _('kana') + _('space') + _('new-kana'), _('help-change-kana')),
        OperationHelp('t', _('kanji'), _('help-known-or-not?{green_tick}').format(green_tick=__green_tick)),
        OperationHelp('R', '', _('help-review')),
        OperationHelp('u', '', _('help-undo')),
        OperationHelp('r', '', _('help-redo')),
        OperationHelp('s', '', _('help-save')),
        OperationHelp('i', '', _('help-info')),
        OperationHelp('en', '', 'English'),
        OperationHelp('es', '', 'español'),
        OperationHelp('fr', '', 'français'),
        OperationHelp('ja', '', '日本語'),
        OperationHelp('h', '', _('help-show-this-help')),
        OperationHelp('q', '', _('help-quit')),
    ]


def __show_help(_command_stack: CommandStack, _vocab: Vocab,
                _params_unused: list[str]) -> OperationResult:
    print(format_help())
    return OperationResult(None, None, False, False)


def format_help() -> str:
    space = '\u3000' if get_locale() == 'ja' else ' '
    help_text = '\n' + _('usage') + ':\n'
    column_widths = __get_help_column_widths()
    for operation_help in __operations_help():
        help_text += ('  ' +
                      operation_help.command.ljust(column_widths.command) +
                      ' ' +
                      operation_help.params.ljust(column_widths.params, space) +
                      space +
                      operation_help.help_text +
                      '\n')
    return help_text


def __get_help_column_widths() -> HelpColumnWidths:
    widths = HelpColumnWidths(0, 0, 0)
    for (command, params, help_text) in __operations_help():
        widths = HelpColumnWidths(
            widths[0] if widths[0] >= len(command) else len(command),
            widths[1] if widths[1] >= len(params) else len(params),
            widths[2] if widths[2] >= len(help_text) else len(help_text),
        )
    return widths


def __operations() -> OperationsDescriptors:
    return {
        'l': OperationDescriptor(
            1,
            None,
            True,
            None,
            _('usage') + ': l ' + _('kanji') + _('bar') + _('kana'),
            __look_up),
        'a': OperationDescriptor(
            1,
            1,
            False,
            None,
            _('usage') + ': a ' + _('kanji'),
            __add),
        'd': OperationDescriptor(
            1,
            1,
            False,
            None,
            _('usage') + ': d ' + _('kanji'),
            __delete),
        'c': OperationDescriptor(
            2,
            2,
            False,
            None,
            _('usage') + ': c ' + _('kanji') + _('space') + _('new-kanji'),
            __change),
        'ak': OperationDescriptor(
            2,
            2,
            False,
            None,
            _('usage') + ': a ' + _('kanji') + _('space') + _('kana'),
            __add_kana),
        'dk': OperationDescriptor(
            2,
            2,
            False,
            None,
            _('usage') + ': d ' + _('kanji') + _('space') + _('kana'),
            __delete_kana),
        'ck': OperationDescriptor(
            3,
            3,
            False,
            None,
            _('usage') + ': c ' + _('kanji') + _('space') + _('kana') + _('space') + _('new-kana'),
            __change_kana),
        't': OperationDescriptor(
            1,
            1,
            False,
            None,
            _('usage') + ': t ' + _('kanji'),
            __toggle_known_status),
        'R': OperationDescriptor(
            0,
            0,
            False,
            None,
            None,
            __review),
        'u': OperationDescriptor(
            0,
            0,
            False,
            lambda command_stack: command_stack.undoable(),
            _('there-is-nothing-to-undo'),
            __undo),
        'r': OperationDescriptor(
            0,
            0,
            False,
            lambda command_stack: command_stack.redoable(),
            _('there-is-nothing-to-redo'),
            __redo),
        's': OperationDescriptor(
            0,
            0,
            False,
            None,
            None,
            __save),
        'i': OperationDescriptor(
            0,
            0,
            False,
            None,
            None,
            __info),
        'en': OperationDescriptor(
            0,
            0,
            False,
            None,
            'English',
            __english),
        'es': OperationDescriptor(
            0,
            0,
            False,
            None,
            'español',
            __spanish),
        'fr': OperationDescriptor(
            0,
            0,
            False,
            None,
            'français',
            __french),
        'ja': OperationDescriptor(
            0,
            0,
            False,
            None,
            '日本語',
            __japanese),
        'h': OperationDescriptor(
            0,
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
