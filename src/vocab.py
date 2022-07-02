import sys
from collections import OrderedDict
from pykakasi import kakasi
from typing import Dict, Final, List, NamedTuple, Optional, Tuple
from unicodedata import normalize


class KanjiInfo(NamedTuple):
    known: bool
    kana_list: List[str]


class Vocab:
    """Vocab stores kanji being learned, the readings being
    learned, and their status of known or not.

    In its interface the word 'kanji' is the thing being
    learned and the things called 'kana' are their
    alternative readings. Words that do not have kanji and
    katakana words are therefore 'kanji' for its interface's
    purposes.
    """

    # Public for tests.
    ITEMS_PER_LIST: Final = 100

    def __init__(self, filename: str) -> None:
        """Loads vocabulary from a file, and raises
        exceptions on format errors."""
        self.__filename: str = filename
        self.__kks: kakasi = kakasi()
        self.__list_to_kanji: Dict[str, List[str]] = {}
        self.__kanji_to_list: Dict[str, str] = {}
        self.__kanji_to_info: Dict[str, KanjiInfo] = {}
        with open(self.__filename) as f:
            lines = f.readlines()
            for line_number, line in enumerate(lines):
                line = line.strip()
                parts = line.split(',')
                if len(parts) < 3:
                    raise Exception(
                        f"line {line_number + 1}: bad line '{line}', {len(parts)} fields, expected at least 4."
                    )
                (list_name, kanji, known) = parts[:3]
                if not Vocab.valid_list_name(list_name):
                    raise Exception(
                        f"line {line_number + 1}: bad list name '{list_name}', expected numeric."
                    )
                if not Vocab.valid_string(kanji):
                    raise Exception(
                        f"line {line_number + 1}: empty kanji '{kanji}'."
                    )
                if known not in ['0', '1']:
                    raise Exception(
                        f"line {line_number + 1}: bad known status '{known}', expected 0 or 1."
                    )
                kana_list = parts[3:]
                if kana_list == ['']:
                    kana_list = []
                if not Vocab.valid_kana_list(kana_list):
                    raise Exception(
                        f"line {line_number + 1}: bad kana list '" +
                        ','.join(kana_list) + "'"
                    )
                if list_name not in self.__list_to_kanji:
                    self.__list_to_kanji[list_name] = []
                self.__list_to_kanji[list_name].append(kanji)
                self.__kanji_to_list[kanji] = list_name
                self.__kanji_to_info[kanji] = KanjiInfo(
                    known == '1', kana_list)

    def save(self) -> None:
        """Saves the vocab back to its original file."""
        with open(self.__filename, 'w') as f:
            for list_name in sorted(self.__list_to_kanji):
                for kanji in sorted(self.__list_to_kanji[list_name]):
                    (known, kana_list) = self.__kanji_to_info[kanji]
                    f.write(
                        normalize(
                            'NFC',
                            f'{list_name},{kanji},{1 if known else 0},{",".join(kana_list)}\n'))

    @property
    def filename(self) -> str:
        return self.__filename

    def get_stats(self) -> Tuple[int, int]:
        """Returns a tuple of (known, learning) counts."""
        known_count = 0
        learning = 0
        for list_name in self.__list_to_kanji:
            for kanji in self.__list_to_kanji[list_name]:
                known = self.__kanji_to_info[kanji][0]
                if known:
                    known_count += 1
                else:
                    learning += 1
        return (known_count, learning)

    def get_list_name(self, kanji: str) -> str:
        "A numeric name of the list that the kanji is in."
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        return self.__kanji_to_list[kanji]

    def __contains__(self, kanji: str) -> bool:
        assert Vocab.valid_string(kanji), kanji
        return kanji in self.__kanji_to_info

    def contains(self, kanji: str, kana: Optional[str] = None) -> bool:
        assert Vocab.valid_string(kanji), kanji
        assert kana is None or Vocab.valid_string(kana), kana
        return kanji in self.__kanji_to_info \
            and (
                kana is None or
                kana in self.__kanji_to_info[kanji][1]
            )

    def search(self, s: str, exact: bool = False) -> List[str]:
        """Search for a string in the kanji and their kana.
        Parameters
        ==========
          exact : True means an exact match.
        """
        assert Vocab.valid_string(s), s
        assert isinstance(exact, bool)
        kanji_found = []
        for kanji in self.__kanji_to_list:
            kana_list = self.__kanji_to_info[kanji][1]
            if not exact and (s in kanji or any(
                    [s in kana for kana in kana_list])) or exact and s == kanji:
                kanji_found.append(kanji)
        return kanji_found

    def add(self, kanji: str, list_name: Optional[str] = None) -> str:
        assert Vocab.valid_string(kanji), kanji
        assert kanji not in self, kanji
        assert list_name is None or Vocab.valid_list_name(list_name), list_name
        if list_name is None:
            list_name = self.new_kanji_list_name()
        kana = ''.join([result['hira']
                       for result in self.__kks.convert(kanji)])
        known = False
        kana_list = [kana] if kana != kanji else []
        self.__list_to_kanji[list_name].append(kanji)
        self.__kanji_to_list[kanji] = list_name
        self.__kanji_to_info[kanji] = KanjiInfo(known, kana_list)
        assert kanji in self, kanji
        return list_name

    def change(self, kanji: str, new_kanji: str) -> None:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        assert Vocab.valid_string(new_kanji), kanji
        assert new_kanji not in self, kanji
        assert new_kanji != kanji
        list_name = self.__kanji_to_list[kanji]
        self.__list_to_kanji[list_name].append(new_kanji)
        self.__list_to_kanji[list_name].remove(kanji)
        self.__kanji_to_list[new_kanji] = list_name
        self.__kanji_to_list.pop(kanji)
        self.__kanji_to_info[new_kanji] = self.__kanji_to_info[kanji]
        self.__kanji_to_info.pop(kanji)
        assert kanji not in self, kanji
        assert new_kanji in self, kanji
        assert self.get_list_name(new_kanji) == list_name

    # Public for tests.
    def new_kanji_list_name(self) -> str:
        "Public for tests."
        list_name = max(self.__list_to_kanji.keys())
        if len(self.__list_to_kanji[list_name]) >= Vocab.ITEMS_PER_LIST:
            list_name = f'{int(list_name) + Vocab.ITEMS_PER_LIST:04d}'
        Vocab.valid_list_name(list_name), list_name
        return list_name

    # Public for tests.
    def count_in_current_list(self) -> int:
        list_name = max(self.__list_to_kanji.keys())
        return len(self.__list_to_kanji[list_name])

    def delete(self, kanji: str) -> str:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        list_name = self.__kanji_to_list[kanji]
        self.__list_to_kanji[list_name].remove(kanji)
        self.__kanji_to_list.pop(kanji)
        self.__kanji_to_info.pop(kanji)
        assert kanji not in self, kanji
        return list_name

    def add_kana(
            self,
            kanji: str,
            kana: str,
            index: Optional[int] = None) -> int:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        assert Vocab.valid_string(kana), kana
        assert not self.contains(kanji, kana), kanji
        assert index is None or Vocab.valid_index(index)
        if index is None:
            index = len(self.__kanji_to_info[kanji][1])
        self.__kanji_to_info[kanji][1].insert(index, kana)
        assert self.contains(kanji, kana), kanji + ', ' + kana
        return self.__kanji_to_info[kanji][1].index(kana)

    def get_kana(self, kanji: str) -> List[str]:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        return self.__kanji_to_info[kanji][1]

    def replace_all_kana(self, kanji: str, kana_list: List[str]) -> None:
        assert Vocab.valid_string(kanji), kanji
        assert Vocab.valid_kana_list(kana_list), kana_list
        known = self.__kanji_to_info[kanji][0]
        self.__kanji_to_info[kanji] = KanjiInfo(known, kana_list)

    def change_kana(self, kanji: str, kana: str, new_kana: str) -> None:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        assert Vocab.valid_string(kana), kana
        assert self.contains(kanji, kana), kanji
        assert Vocab.valid_string(new_kana), kana
        assert not self.contains(kanji, new_kana), kanji
        known, kana_list = self.__kanji_to_info[kanji]
        kana_list[kana_list.index(kana)] = new_kana
        self.__kanji_to_info[kanji] = KanjiInfo(known, kana_list)
        assert not self.contains(kanji, kana), kanji
        assert self.contains(kanji, new_kana), kanji

    def delete_kana(self, kanji: str, kana: str) -> int:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        assert Vocab.valid_string(kana), kana
        assert self.contains(kanji, kana), kanji
        index = self.__kanji_to_info[kanji][1].index(kana)
        self.__kanji_to_info[kanji][1].remove(kana)
        assert not self.contains(kanji, kana), kanji
        return index

    def is_known(self, kanji: str) -> bool:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        return self.__kanji_to_info[kanji][0]

    def toggle_known(self, kanji: str) -> bool:
        assert Vocab.valid_string(kanji), kanji
        assert kanji in self, kanji
        known, kana_list = self.__kanji_to_info[kanji]
        new_known = not known
        self.__kanji_to_info[kanji] = KanjiInfo(new_known, kana_list)
        return new_known

    def set_known(self, kanji: str, known: bool) -> None:
        assert Vocab.valid_string(kanji), kanji
        assert isinstance(known, bool)
        kana_list = self.__kanji_to_info[kanji][1]
        self.__kanji_to_info[kanji] = KanjiInfo(known, kana_list)

    @staticmethod
    def valid_index(i: int) -> bool:
        return isinstance(i, int) and i >= 0

    @staticmethod
    def valid_kana_list(kana_list: List[str]) -> bool:
        return isinstance(kana_list, list) and \
            all(isinstance(k, str) and len(k) > 0 for k in kana_list)

    @staticmethod
    def valid_list_name(list_name: str) -> bool:
        return isinstance(list_name, str) and \
            list_name.isnumeric()

    @staticmethod
    def valid_string(s: str) -> bool:
        return isinstance(s, str) and len(s) > 0
