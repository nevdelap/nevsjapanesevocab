from abc import ABC, abstractmethod
from typing import Optional

from colors import color  # type: ignore

from localisation import _
from vocab import Vocab


class Command(ABC):
    """Base class for undoable and redoable commands."""

    def __init__(self, vocab: Vocab) -> None:
        self.vocab: Vocab = vocab

    @abstractmethod
    def do(self) -> None:
        pass

    def undo(self) -> str:
        """Undoes the last command and returns a user
        readable string describing what it did."""
        return self._undone_message()

    def redo(self) -> str:
        """Re-does the last command undone and returns a
        user readable string describing what it did."""
        return self._redone_message()

    @abstractmethod
    def _undone_message(self) -> str:
        pass

    @abstractmethod
    def _redone_message(self) -> str:
        pass


class CommandStack:
    """Command stack for managing undoable/redoable
    commands."""

    def __init__(self) -> None:
        self.__commands: list[Command] = []
        self.__current: int = -1
        assert not self.undoable()
        assert not self.redoable()

    def current(self) -> int:
        """Returns the index of the current comment that
        will be undone or re-done. For tests."""
        return self.__current

    def do(self, command: Command) -> None:
        self.__commands = self.__commands[: self.__current + 1]
        self.__commands.append(command)
        self.__current += 1
        self.__commands[self.__current].do()
        assert self.undoable()
        assert not self.redoable()

    def undoable(self) -> bool:
        return self.__current >= 0

    def redoable(self) -> bool:
        return self.__current < len(self.__commands) - 1

    def undo(self) -> str:
        assert self.undoable()
        message = self.__commands[self.__current].undo()
        self.__current -= 1
        assert self.redoable()
        return message

    def redo(self) -> str:
        assert self.redoable()
        self.__current += 1
        message = self.__commands[self.__current].redo()
        assert self.undoable()
        return message


class AddCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__list_name: Optional[str] = None

    def do(self) -> None:
        self.__list_name = self.vocab.add(self.__kanji)

    def undo(self) -> str:
        self.vocab.delete(self.__kanji)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.add(self.__kanji, self.__list_name)
        return self._redone_message()

    def _undone_message(self) -> str:
        return _("{kanji}-has-been-deleted-from-list-{list_name}").format(
            kanji=self.__kanji, list_name=self.__list_name
        )

    def _redone_message(self) -> str:
        return _("{kanji}-added-to-list-{list_name}").format(
            kanji=self.__kanji, list_name=self.__list_name
        )


class DeleteCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__known: bool = self.vocab.is_known(kanji)
        self.__kana: list[str] = list(self.vocab.get_kana(kanji))
        self.__list_name: Optional[str] = None

    def do(self) -> None:
        self.__list_name = self.vocab.delete(self.__kanji)

    def undo(self) -> str:
        self.vocab.add(self.__kanji, self.__list_name)
        self.vocab.set_known(self.__kanji, self.__known)
        self.vocab.replace_all_kana(self.__kanji, self.__kana)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.delete(self.__kanji)
        return self._redone_message()

    def _undone_message(self) -> str:
        return _("{kanji}-added-to-list-{list_name}").format(
            kanji=self.__kanji, list_name=self.__list_name
        )

    def _redone_message(self) -> str:
        return _("{kanji}-has-been-deleted-from-list-{list_name}").format(
            kanji=self.__kanji, list_name=self.__list_name
        )


class ChangeCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str, new_kanji: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__new_kanji: str = new_kanji

    def do(self) -> None:
        self.redo()

    def undo(self) -> str:
        self.vocab.change(self.__new_kanji, self.__kanji)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.change(self.__kanji, self.__new_kanji)
        return self._redone_message()

    def _undone_message(self) -> str:
        return _("{new_kanji}-changed-back-to-{kanji}").format(
            new_kanji=self.__new_kanji, kanji=self.__kanji
        )

    def _redone_message(self) -> str:
        return _("{kanji}-changed-to-{new_kanji}").format(
            kanji=self.__kanji, new_kanji=self.__new_kanji
        )


class AddKanaCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str, kana: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__kana: str = kana
        self.__index: int = -1

    def do(self) -> None:
        self.__index = self.vocab.add_kana(self.__kanji, self.__kana)

    def undo(self) -> str:
        self.vocab.delete_kana(self.__kanji, self.__kana)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.add_kana(self.__kanji, self.__kana, self.__index)
        return self._redone_message()

    def _undone_message(self) -> str:
        return _("{kana}-deleted-from-{kanji}").format(
            kanji=self.__kanji, kana=self.__kana
        )

    def _redone_message(self) -> str:
        return _("{kana}-added-to-{kanji}").format(kanji=self.__kanji, kana=self.__kana)


class ChangeKanaCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str, kana: str, new_kana: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__kana: str = kana
        self.__new_kana: str = new_kana

    def do(self) -> None:
        self.redo()

    def undo(self) -> str:
        self.vocab.change_kana(self.__kanji, self.__new_kana, self.__kana)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.change_kana(self.__kanji, self.__kana, self.__new_kana)
        return self._redone_message()

    def _undone_message(self) -> str:
        return _("{new_kana}-changed-back-to-{kana}-for-{kanji}").format(
            kanji=self.__kanji, kana=self.__kana, new_kana=self.__new_kana
        )

    def _redone_message(self) -> str:
        return _("{kana}-changed-to-{new_kana}-for-{kanji}").format(
            kanji=self.__kanji, kana=self.__kana, new_kana=self.__new_kana
        )


class DeleteKanaCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str, kana: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__kana: str = kana
        self.__index: int = -1

    def do(self) -> None:
        self.__index = self.vocab.delete_kana(self.__kanji, self.__kana)

    def undo(self) -> str:
        self.vocab.add_kana(self.__kanji, self.__kana, self.__index)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.delete_kana(self.__kanji, self.__kana)
        return self._redone_message()

    def _undone_message(self) -> str:
        return _("{kana}-added-to-{kanji}").format(kanji=self.__kanji, kana=self.__kana)

    def _redone_message(self) -> str:
        return _("{kana}-deleted-from-{kanji}").format(
            kanji=self.__kanji, kana=self.__kana
        )


class ToggleKnownCommand(Command):
    def __init__(self, vocab: Vocab, kanji: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__known: bool = vocab.is_known(kanji)

    def do(self) -> None:
        self.redo()

    def undo(self) -> str:
        self.vocab.set_known(self.__kanji, self.__known)
        return self._undone_message()

    def redo(self) -> str:
        self.vocab.set_known(self.__kanji, not self.__known)
        return self._redone_message()

    def _undone_message(self) -> str:
        return self.__message(True)

    def _redone_message(self) -> str:
        return self.__message(False)

    def __message(self, redo: bool) -> str:
        green_tick = color("✓", fg="green")
        known_status = (
            _("already-known") + f"({green_tick})"
            if redo == self.__known
            else _("unknown")
        )
        return _("toggled-the-{known_status}-of-{kanji}").format(
            kanji=self.__kanji, known_status=known_status
        )
