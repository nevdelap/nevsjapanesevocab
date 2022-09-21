import pytest
from test_helpers import strip_ansi_terminal_escapes

from commands import AddCommand
from commands import AddKanaCommand
from commands import ChangeCommand
from commands import ChangeKanaCommand
from commands import CommandStack
from commands import DeleteCommand
from commands import DeleteKanaCommand
from commands import ToggleKnownCommand
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    return Vocab("tests/test_data/vocab_good.csv")


@pytest.fixture
def command_stack() -> CommandStack:
    return CommandStack()


def test_new_command(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, "new"))
    assert command_stack.current() == 0
    assert vocab.contains("new")
    message = command_stack.undo()
    assert message == f"new-has-been-deleted-from-list-{vocab.new_kanji_list_name()}"
    assert command_stack.current() == -1
    assert not vocab.contains("new")
    message = command_stack.redo()
    assert message == f"new-added-to-list-{vocab.new_kanji_list_name()}"
    assert command_stack.current() == 0
    assert vocab.contains("new")
    command_stack.undo()
    assert command_stack.current() == -1
    assert not vocab.contains("new")


def test_change_command(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, "new"))
    assert command_stack.current() == 0
    assert vocab.contains("new")
    command_stack.do(ChangeCommand(vocab, "new", "NEW"))
    assert command_stack.current() == 1
    assert vocab.contains("NEW")
    message = command_stack.undo()
    assert message == "NEW-changed-back-to-new"
    assert command_stack.current() == 0
    assert vocab.contains("new")
    assert not vocab.contains("NEW")
    message = command_stack.redo()
    assert message == "new-changed-to-NEW"
    assert command_stack.current() == 1
    assert not vocab.contains("new")
    assert vocab.contains("NEW")
    command_stack.undo()
    assert command_stack.current() == 0
    assert vocab.contains("new")
    assert not vocab.contains("NEW")


def test_delete_command(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    vocab.toggle_known("送る")
    vocab.add_kana("送る", "new")
    list_name = vocab.get_list_name("送る")
    known = vocab.is_known("送る")
    kana = vocab.get_kana("送る")
    command_stack.do(DeleteCommand(vocab, "送る"))
    assert command_stack.current() == 0
    assert not vocab.contains("送る")
    message = command_stack.undo()
    assert message == "送る-added-to-list-0100"
    assert command_stack.current() == -1
    assert vocab.contains("送る")
    assert vocab.get_list_name("送る") == list_name
    assert vocab.is_known("送る") == known
    assert vocab.get_kana("送る") == kana
    message = command_stack.redo()
    assert message == "送る-has-been-deleted-from-list-0100"
    assert command_stack.current() == 0
    assert not vocab.contains("送る")
    command_stack.undo()
    assert command_stack.current() == -1
    assert vocab.contains("送る")
    assert vocab.get_list_name("送る") == list_name
    assert vocab.is_known("送る") == known
    assert vocab.get_kana("送る") == kana


def test_undo_redo(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, "new"))
    assert command_stack.current() == 0
    command_stack.do(DeleteCommand(vocab, "new"))
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


def test_new_kana_command(vocab: Vocab, command_stack: CommandStack) -> None:
    assert vocab.get_kana("送る") == ["おくる"]
    command_stack.do(AddKanaCommand(vocab, "送る", "new"))
    assert vocab.contains("送る", "new")
    assert vocab.get_kana("送る") == ["おくる", "new"]
    message = command_stack.undo()
    assert message == "new-deleted-from-送る"
    assert not vocab.contains("送る", "new")
    assert vocab.get_kana("送る") == ["おくる"]
    message = command_stack.redo()
    assert message == "new-added-to-送る"
    assert vocab.contains("送る", "new")
    assert vocab.get_kana("送る") == ["おくる", "new"]
    command_stack.undo()
    assert not vocab.contains("送る", "new")
    assert vocab.get_kana("送る") == ["おくる"]


def test_change_kana_command(vocab: Vocab, command_stack: CommandStack) -> None:
    assert command_stack.current() == -1
    command_stack.do(AddCommand(vocab, "new"))
    command_stack.do(AddKanaCommand(vocab, "new", "kana"))
    command_stack.do(AddKanaCommand(vocab, "new", "kana2"))
    assert command_stack.current() == 2
    assert vocab.contains("new", "kana")
    assert vocab.contains("new", "kana2")
    assert not vocab.contains("new", "kana3")
    assert ["kana", "kana2"] == vocab.get_kana("new")
    command_stack.do(ChangeKanaCommand(vocab, "new", "kana", "kana3"))
    assert command_stack.current() == 3
    assert not vocab.contains("new", "kana")
    assert vocab.contains("new", "kana2")
    assert vocab.contains("new", "kana3")
    assert ["kana3", "kana2"] == vocab.get_kana("new")
    message = command_stack.undo()
    assert message == "kana3-changed-back-to-kana-for-new"
    assert command_stack.current() == 2
    assert vocab.contains("new", "kana")
    assert vocab.contains("new", "kana2")
    assert not vocab.contains("new", "kana3")
    message = command_stack.redo()
    assert message == "kana-changed-to-kana3-for-new"
    assert command_stack.current() == 3
    assert not vocab.contains("new", "kana")
    assert vocab.contains("new", "kana2")
    assert vocab.contains("new", "kana3")
    message = command_stack.undo()
    assert message == "kana3-changed-back-to-kana-for-new"
    assert command_stack.current() == 2
    assert vocab.contains("new", "kana")
    assert vocab.contains("new", "kana2")
    assert not vocab.contains("new", "kana3")


def test_delete_kana_command(vocab: Vocab, command_stack: CommandStack) -> None:
    assert vocab.get_kana("送る") == ["おくる"]
    command_stack.do(AddKanaCommand(vocab, "送る", "new"))
    assert vocab.contains("送る", "new")
    assert vocab.get_kana("送る") == ["おくる", "new"]
    command_stack.do(DeleteKanaCommand(vocab, "送る", "おくる"))
    assert vocab.get_kana("送る") == ["new"]
    command_stack.do(AddKanaCommand(vocab, "送る", "new2"))
    assert vocab.contains("送る", "new2")
    assert vocab.get_kana("送る") == ["new", "new2"]
    command_stack.do(DeleteKanaCommand(vocab, "送る", "new"))
    assert not vocab.contains("送る", "new")
    assert vocab.get_kana("送る") == ["new2"]
    message = command_stack.undo()
    assert message == "new-added-to-送る"
    assert vocab.get_kana("送る") == ["new", "new2"]
    command_stack.undo()
    assert vocab.get_kana("送る") == ["new"]
    command_stack.undo()
    assert vocab.get_kana("送る") == ["おくる", "new"]
    command_stack.undo()
    assert not command_stack.undoable()
    message = command_stack.redo()
    assert message == "new-added-to-送る"
    assert vocab.get_kana("送る") == ["おくる", "new"]
    command_stack.redo()
    assert vocab.get_kana("送る") == ["new"]
    command_stack.redo()
    assert vocab.get_kana("送る") == ["new", "new2"]
    command_stack.redo()
    assert vocab.get_kana("送る") == ["new2"]
    assert not command_stack.redoable()
    command_stack.undo()
    command_stack.undo()
    command_stack.undo()
    command_stack.undo()
    assert not command_stack.undoable()
    assert vocab.get_kana("送る") == ["おくる"]


def test_toggle_status_command(vocab: Vocab, command_stack: CommandStack) -> None:
    known = vocab.is_known("送る")
    command_stack.do(ToggleKnownCommand(vocab, "送る"))
    assert vocab.is_known("送る") == (not known)
    message = command_stack.undo()
    assert message == "toggled-the-unknown-of-送る"
    assert vocab.is_known("送る") == known
    message = command_stack.redo()
    assert strip_ansi_terminal_escapes(message) == "toggled-the-already-known(✓)-of-送る"
    assert vocab.is_known("送る") == (not known)
    command_stack.undo()
    assert vocab.is_known("送る") == known
