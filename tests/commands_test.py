import pytest
from commands import *
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    return Vocab('tests/test_data/vocab_good.csv')


@pytest.fixture
def command_stack() -> CommandStack:
    return CommandStack()


def test_NewCommand(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, 'new'))
    assert command_stack.current() == 0
    assert vocab.contains('new')
    message = command_stack.undo()
    assert message == f'newはリスト{vocab.new_kanji_list_name()}から削除した。'
    assert command_stack.current() == -1
    assert not vocab.contains('new')
    message = command_stack.redo()
    assert message == f'newはリスト{vocab.new_kanji_list_name()}に追加した。'
    assert command_stack.current() == 0
    assert vocab.contains('new')
    command_stack.undo()
    assert command_stack.current() == -1
    assert not vocab.contains('new')


def test_ChangeCommand(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, 'new'))
    assert command_stack.current() == 0
    assert vocab.contains('new')
    message = command_stack.undo()
    assert message == f'newはリスト{vocab.new_kanji_list_name()}から削除した。'
    assert command_stack.current() == -1
    assert not vocab.contains('new')
    message = command_stack.redo()
    assert message == f'newはリスト{vocab.new_kanji_list_name()}に追加した。'
    assert command_stack.current() == 0
    assert vocab.contains('new')
    command_stack.undo()
    assert command_stack.current() == -1
    assert not vocab.contains('new')


def test_DeleteCommand(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    vocab.toggle_known('送る')
    vocab.add_kana('送る', 'new')
    list_name = vocab.get_list_name('送る')
    known = vocab.is_known('送る')
    kana = vocab.get_kana('送る')
    command_stack.do(DeleteCommand(vocab, '送る'))
    assert command_stack.current() == 0
    assert not vocab.contains('送る')
    message = command_stack.undo()
    assert message == '送るはリスト0100に追加した。'
    assert command_stack.current() == -1
    assert vocab.contains('送る')
    assert vocab.get_list_name('送る') == list_name
    assert vocab.is_known('送る') == known
    assert vocab.get_kana('送る') == kana
    message = command_stack.redo()
    assert message == '送るはリスト0100から削除した。'
    assert command_stack.current() == 0
    assert not vocab.contains('送る')
    command_stack.undo()
    assert command_stack.current() == -1
    assert vocab.contains('送る')
    assert vocab.get_list_name('送る') == list_name
    assert vocab.is_known('送る') == known
    assert vocab.get_kana('送る') == kana


def test_undo_redo(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, 'new'))
    assert command_stack.current() == 0
    command_stack.do(DeleteCommand(vocab, 'new'))
    assert command_stack.current() == 1
    assert command_stack.undoable()
    assert not command_stack.redoable()
    command_stack.undo()
    assert command_stack.current() == 0
    assert command_stack.undoable()
    assert command_stack.redoable()
    command_stack.undo()
    assert command_stack.current() == -1
    assert not command_stack.undoable()
    assert command_stack.redoable()
    command_stack.redo()
    assert command_stack.undoable()
    assert command_stack.redoable()
    command_stack.redo()
    assert command_stack.undoable()
    assert not command_stack.redoable()


def test_NewKanaCommand(vocab: Vocab, command_stack: CommandStack) -> None:
    assert vocab.get_kana('送る') == ['おくる']
    command_stack.do(AddKanaCommand(vocab, '送る', 'new'))
    assert vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる', 'new']
    message = command_stack.undo()
    assert message == 'newは送るから削除した。'
    assert not vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる']
    message = command_stack.redo()
    assert message == 'newは送るに追加した。'
    assert vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる', 'new']
    command_stack.undo()
    assert not vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる']


def test_ChangeKanaCommand(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, 'new'))
    command_stack.do(AddKanaCommand(vocab, 'new', 'kana'))
    command_stack.do(AddKanaCommand(vocab, 'new', 'kana2'))
    assert command_stack.current() == 2
    assert vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert not vocab.contains('new', 'kana3')
    assert ['kana', 'kana2'] == vocab.get_kana('new')
    command_stack.do(ChangeKanaCommand(vocab, 'new', 'kana', 'kana3'))
    assert command_stack.current() == 3
    assert not vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert vocab.contains('new', 'kana3')
    assert ['kana3', 'kana2'] == vocab.get_kana('new')
    message = command_stack.undo()
    assert message == 'newはkana3をkanaに戻した。'
    assert command_stack.current() == 2
    assert vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert not vocab.contains('new', 'kana3')
    message = command_stack.redo()
    assert message == 'newはkanaをkana3に変更した。'
    assert command_stack.current() == 3
    assert not vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert vocab.contains('new', 'kana3')


def test_DeleteKanaCommand(vocab: Vocab, command_stack: CommandStack) -> None:
    assert vocab.get_kana('送る') == ['おくる']
    command_stack.do(AddKanaCommand(vocab, '送る', 'new'))
    assert vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる', 'new']
    command_stack.do(DeleteKanaCommand(vocab, '送る', 'おくる'))
    assert vocab.get_kana('送る') == ['new']
    command_stack.do(AddKanaCommand(vocab, '送る', 'new2'))
    assert vocab.contains('送る', 'new2')
    assert vocab.get_kana('送る') == ['new', 'new2']
    command_stack.do(DeleteKanaCommand(vocab, '送る', 'new'))
    assert not vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['new2']
    message = command_stack.undo()
    assert message == 'newは送るに追加した。'
    assert vocab.get_kana('送る') == ['new', 'new2']
    command_stack.undo()
    assert vocab.get_kana('送る') == ['new']
    command_stack.undo()
    assert vocab.get_kana('送る') == ['おくる', 'new']
    command_stack.undo()
    assert not command_stack.undoable()
    message = command_stack.redo()
    assert message == 'newは送るに追加した。'
    assert vocab.get_kana('送る') == ['おくる', 'new']
    command_stack.redo()
    assert vocab.get_kana('送る') == ['new']
    command_stack.redo()
    assert vocab.get_kana('送る') == ['new', 'new2']
    command_stack.redo()
    assert vocab.get_kana('送る') == ['new2']
    assert not command_stack.redoable()
    command_stack.undo()
    command_stack.undo()
    command_stack.undo()
    command_stack.undo()
    assert not command_stack.undoable()
    assert vocab.get_kana('送る') == ['おくる']


def test_ToggleStatusCommand(vocab: Vocab,
                             command_stack: CommandStack) -> None:
    known = vocab.is_known('送る')
    command_stack.do(ToggleKnownCommand(vocab, '送る'))
    assert vocab.is_known('送る') == (not known)
    message = command_stack.undo()
    assert message == '送るのステータスが未知に変更された。'
    assert vocab.is_known('送る') == known
    message = command_stack.redo()
    assert message == '送るのステータスが既知(\x1b[32m✓\x1b[0m)に変更された。'
    assert vocab.is_known('送る') == (not known)
    command_stack.undo()
    assert vocab.is_known('送る') == known
