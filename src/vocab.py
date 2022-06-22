import pykakasi
import sys
import typing
from collections import OrderedDict
from unicodedata import normalize


class Vocab:
    """Vocab stores kanji being learned, the readings being
    learned, and their status of known or not.

    In its interface the word 'kanji' is the thing being
    learned and the things called 'kana' are their
    alternative readings. Words that do not have kanji and
    katakana words are therefore 'kanji' for its interface's
    purposes.
    """

    __itemsPerList: int = 100

    def __init__(self, filename: str) -> None:
        """Loads vocabulary from a file, and raises
        exceptions on format errors."""
        self.__filename = filename
        self.__kks = pykakasi.kakasi()
        self.__list_to_kanji = OrderedDict()
        self.__kanji_to_list = {}
        self.__kanji_to_info = {}
        with open(self.__filename) as f:
            lines = f.readlines()
            for line_number, line in enumerate(lines):
                line = line.strip()
                parts = line.split(',')
                if len(parts) < 3:
                    raise Exception(
                        f"line {line_number + 1}: bad line '{line}', {len(parts)} fields, expected at least 4."
                    )
                list_name, kanji, known = parts[:3]
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
                known = known == '1'
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
                self.__kanji_to_info[kanji] = (known, kana_list)

    def save(self) -> None:
        """Saves the vocab back to its original file."""
        with open(self.__filename, 'w') as f:
            for list_name in self.__list_to_kanji:
                for kanji in self.__list_to_kanji[list_name]:
                    known, kana_list = self.__kanji_to_info[kanji]
                    known = 1 if known else 0
                    kana_list = ','.join(kana_list)
                    f.write(
                        normalize('NFC',
                            '%s,%s,%s,%s\n' % (list_name, kanji, known, kana_list)
                            )
                    )

    def get_stats(self) -> (int, int, int):
        """Returns a tuple of (known, learning, total)
        counts."""
        known_count = 0
        learning = 0
        for list_name in self.__list_to_kanji:
            for kanji in self.__list_to_kanji[list_name]:
                known = self.__kanji_to_info[kanji][0]
                if known:
                    known_count += 1
                else:
                    learning += 1
        return (known_count, learning, known_count + learning)

    def get_list_name(self, kanji: str) -> str:
        "A numeric name of the list that the kanji is in."
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        return self.__kanji_to_list[kanji]

    def get_known(self, kanji: str) -> bool:
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        return self.__kanji_to_info[kanji][0]

    def set_known(self, kanji: str, known: bool) -> None:
        assert Vocab.valid_string(kanji), kanji
        assert isinstance(known, bool)
        kana_list = self.__kanji_to_info[kanji][1]
        self.__kanji_to_info[kanji] = (known, kana_list)

    def get_kana(self, kanji: str) -> list:
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        return self.__kanji_to_info[kanji][1]

    def replace_kana(self, kanji: str, kana_list: list) -> None:
        assert Vocab.valid_string(kanji), kanji
        assert Vocab.valid_kana_list(kana_list), kana_list
        known = self.__kanji_to_info[kanji][0]
        self.__kanji_to_info[kanji] = (known, kana_list)

    def contains(self, kanji: str, kana: str = None) -> bool:
        assert Vocab.valid_string(kanji), kanji
        assert kana is None or Vocab.valid_string(kana), kana
        return kanji in self.__kanji_to_info \
            and (
                kana is None or
                kana in self.__kanji_to_info[kanji][1]
            )

    def search(self, s, exact: bool = False) -> [str]:
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

    def new(self, kanji: str, list_name: str = None) -> str:
        assert Vocab.valid_string(kanji), kanji
        assert not self.contains(kanji), kanji
        assert list_name is None or Vocab.valid_list_name(list_name), list_name
        if list_name is None:
            list_name = self.new_kanji_list_name()
        kana = ''.join([result['hira']
                       for result in self.__kks.convert(kanji)])
        kana_list = [kana] if kana != kanji else []
        self.__list_to_kanji[list_name].append(kanji)
        self.__kanji_to_list[kanji] = list_name
        self.__kanji_to_info[kanji] = (False, kana_list)
        assert self.contains(kanji), kanji
        return list_name

    def new_kanji_list_name(self) -> str:
        "Public for tests."
        list_name = max(self.__list_to_kanji.keys())
        if len(self.__list_to_kanji) >= Vocab.__itemsPerList:
            list_name = '%04d' % (int(list_name) + Vocab.__itemsPerList)
        Vocab.valid_list_name(list_name), list_name
        return list_name

    def delete(self, kanji: str) -> str:
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        list_name = self.__kanji_to_list[kanji]
        self.__list_to_kanji[list_name].remove(kanji)
        self.__kanji_to_list.pop(kanji)
        self.__kanji_to_info.pop(kanji)
        assert not self.contains(kanji), kanji
        return list_name

    def new_kana(self, kanji: str, kana: str, index: int = None) -> int:
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        assert Vocab.valid_string(kana), kana
        assert not self.contains(kanji, kana), kanji
        assert index is None or Vocab.valid_index(index)
        if index is None:
            index = len(self.__kanji_to_info[kanji][1])
        self.__kanji_to_info[kanji][1].insert(index, kana)
        assert self.contains(kanji, kana), kanji + ', ' + kana
        return self.__kanji_to_info[kanji][1].index(kana)

    def delete_kana(self, kanji: str, kana: str) -> int:
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        assert Vocab.valid_string(kana), kana
        assert self.contains(kanji, kana), kanji
        index = self.__kanji_to_info[kanji][1].index(kana)
        self.__kanji_to_info[kanji][1].remove(kana)
        assert not self.contains(kanji, kana), kanji
        return index

    def toggle_known(self, kanji: str) -> bool:
        assert Vocab.valid_string(kanji), kanji
        assert self.contains(kanji), kanji
        known, kana_list = self.__kanji_to_info[kanji]
        new_known = not known
        self.__kanji_to_info[kanji] = (new_known, kana_list)
        return new_known

    def valid_index(i: int) -> bool:
        return isinstance(i, int) and i >= 0

    def valid_kana_list(kana_list: list) -> bool:
        return isinstance(kana_list, list) and \
            all(isinstance(k, str) and len(k) > 0 for k in kana_list)

    def valid_list_name(list_name) -> bool:
        return isinstance(list_name, str) and \
            list_name.isnumeric()

    def valid_string(s: str) -> bool:
        return isinstance(s, str) and len(s) > 0
