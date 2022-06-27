from abc import ABC, abstractmethod
from colors import color  # type: ignore
from typing import List, Optional
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
        self.__commands: List[Command] = []
        self.__current: int = -1
        assert not self.undoable()
        assert not self.redoable()

    def current(self) -> int:
        """Returns the index of the current comment that
        will be undone or re-done. For tests."""
        return self.__current

    def do(self, command: Command) -> None:
        self.__commands = self.__commands[:self.__current + 1]
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
        return f'{self.__kanji}はリスト{self.__list_name}から削除した。'

    def _redone_message(self) -> str:
        return f'{self.__kanji}はリスト{self.__list_name}に追加した。'


class DeleteCommand(Command):

    def __init__(self, vocab: Vocab, kanji: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__known: bool = self.vocab.get_known(kanji)
        self.__kana: List[str] = self.vocab.get_kana(kanji)
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
        return f'{self.__kanji}はリスト{self.__list_name}に追加した。'

    def _redone_message(self) -> str:
        return f'{self.__kanji}はリスト{self.__list_name}から削除した。'


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
        return f'{self.__new_kanji}を{self.__kanji}に戻した。'

    def _redone_message(self) -> str:
        return f'{self.__kanji}を{self.__new_kanji}に変更した。'


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
        return f'{self.__kana}は{self.__kanji}から削除した。'

    def _redone_message(self) -> str:
        return f'{self.__kana}は{self.__kanji}に追加した。'


class ChangeKanaCommand(Command):

    def __init__(
            self,
            vocab: Vocab,
            kanji: str,
            kana: str,
            new_kana: str) -> None:
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
        return f'{self.__kanji}は{self.__new_kana}を{self.__kana}に戻した。'

    def _redone_message(self) -> str:
        return f'{self.__kanji}は{self.__kana}を{self.__new_kana}に変更した。'


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
        return f'{self.__kana}は{self.__kanji}に追加した。'

    def _redone_message(self) -> str:
        return f'{self.__kana}は{self.__kanji}から削除した。'


class ToggleKnownCommand(Command):

    def __init__(self, vocab: Vocab, kanji: str) -> None:
        Command.__init__(self, vocab)
        self.__kanji: str = kanji
        self.__known: bool = vocab.get_known(kanji)

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

    def __message(self, redo) -> str:
        return f'{self.__kanji}のステータスが%sに変更された。' % ('既知(%s)' % color(
            '✓', fg='green') if redo == self.__known else '未知')
