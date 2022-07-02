import contextlib
import io
import pytest
from typing import List, Tuple
from unittest_data_provider import data_provider  # type: ignore
from vocab import Vocab


@pytest.fixture
def vocab() -> Vocab:
    return Vocab('tests/test_data/vocab_good.csv')


def test_new_kanji_list_name(vocab: Vocab) -> None:
    assert vocab.new_kanji_list_name() == '0100'


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


@pytest.mark.parametrize("filename, expected_error",
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
