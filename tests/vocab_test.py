import contextlib
import io
import os
import pathlib
import pytest
from typing import List, Tuple
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    return Vocab('tests/test_data/vocab_good.csv')


def test_new_kanji_list_name(vocab: Vocab) -> None:
    assert vocab.new_kanji_list_name() == '0100'
    with open(vocab.filename) as f:
        assert vocab.count_in_current_list() == len(f.readlines())
    for i in range(
            0,
            vocab.ITEMS_PER_LIST - vocab.count_in_current_list() - 1):
        vocab.add(f'new{i}')
    assert vocab.count_in_current_list() == vocab.ITEMS_PER_LIST - 1
    assert vocab.new_kanji_list_name() == '0100'
    vocab.add(f'tipitover')
    vocab.count_in_current_list() == 1
    assert vocab.new_kanji_list_name() == '0200'
    assert vocab.add('砂糖') == '0200'


def test_contains(vocab: Vocab) -> None:
    assert '送る' in vocab
    assert 'junk' not in vocab
    assert vocab.contains('送る', 'おくる')
    assert not vocab.contains('送る', 'junk')


def test_add_delete_kanji(vocab: Vocab) -> None:
    assert not vocab.contains('new')
    list_name = vocab.add('new')
    assert vocab.get_list_name('new') == list_name
    assert not vocab.is_known('new')
    assert vocab.toggle_known('new')
    assert vocab.is_known('new')
    assert not vocab.toggle_known('new')
    assert not vocab.is_known('new')
    assert vocab.contains('new')
    assert vocab.delete('new') == list_name


def test_change_kanji(vocab: Vocab) -> None:
    assert not vocab.contains('new')
    list_name = vocab.add('new')
    vocab.add_kana('new', 'kana')
    vocab.add_kana('new', 'kana2')
    assert vocab.contains('new')
    assert vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert not vocab.contains('NEW')
    assert not vocab.contains('NEW', 'kana')
    assert not vocab.contains('NEW', 'kana2')
    vocab.change('new', 'NEW')
    assert not vocab.contains('new')
    assert not vocab.contains('new', 'kana')
    assert not vocab.contains('new', 'kana2')
    assert vocab.contains('NEW')
    assert vocab.contains('NEW', 'kana')
    assert vocab.contains('NEW', 'kana2')


def test_add_delete_kana(vocab: Vocab) -> None:
    assert not vocab.contains('送る', 'new')
    index = vocab.add_kana('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる', 'new']
    index2 = vocab.add_kana('送る', 'new2')
    assert vocab.contains('送る', 'new2')
    assert vocab.get_kana('送る') == ['おくる', 'new', 'new2']
    assert vocab.delete_kana('送る', 'new2') == index2
    assert not vocab.contains('送る', 'new2')
    assert vocab.get_kana('送る') == ['おくる', 'new']
    index2 = vocab.add_kana('送る', 'new2')
    assert vocab.delete_kana('送る', 'new') == index
    assert not vocab.contains('送る', 'new')
    assert vocab.get_kana('送る') == ['おくる', 'new2']
    assert vocab.delete_kana('送る', 'new2') == index
    assert not vocab.contains('送る', 'new2')
    assert vocab.get_kana('送る') == ['おくる']


def test_change_kana(vocab: Vocab) -> None:
    assert not vocab.contains('new')
    list_name = vocab.add('new')
    vocab.add_kana('new', 'kana')
    vocab.add_kana('new', 'kana2')
    assert vocab.contains('new')
    assert vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert not vocab.contains('new', 'kana3')
    assert ['kana', 'kana2'] == vocab.get_kana('new')
    vocab.change_kana('new', 'kana', 'kana3')
    assert vocab.contains('new')
    assert not vocab.contains('new', 'kana')
    assert vocab.contains('new', 'kana2')
    assert vocab.contains('new', 'kana3')
    assert ['kana3', 'kana2'] == vocab.get_kana('new')


@pytest.mark.parametrize('filename, expected_error',
                         [('vocab_bad_kana.csv',
                           "line 3: bad kana list ',,'"),
                          ('vocab_bad_kanji.csv',
                           "line 3: empty kanji ''."),
                          ('vocab_bad_line.csv',
                           "line 3: bad line '0100,送る', 2 fields, expected at least 4."),
                          ('vocab_bad_list_name.csv',
                           "line 3: bad list name 'asdd', expected numeric.")])
def test_bad_files(filename: str, expected_error: str) -> None:
    with pytest.raises(Exception) as e_info:
        Vocab(f'tests/test_data/{filename}')
    assert expected_error in str(e_info)


def test_save(tmp_path: pathlib.Path, vocab: Vocab) -> None:
    tmp_filename = str(tmp_path / 'new.csv')
    vocab.add('new')
    vocab.add_kana('new', 'kana')
    vocab.add_kana('new', 'new')
    vocab.add_kana('new', 'kana2')
    vocab.add('new2')
    vocab.toggle_known('new2')
    vocab.save(tmp_filename)
    vocab2 = Vocab(tmp_filename)
    assert 'new' in vocab2
    # expressly not kana 'new' that duplicates the kanji 'new'.
    assert vocab2.get_kana('new') == ['kana', 'kana2']
    assert not vocab2.is_known('new')
    assert 'new2' in vocab2
    assert vocab2.is_known('new2')
