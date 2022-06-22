import contextlib
import io
import unittest
from main import replace_indices
from unittest_data_provider import data_provider
from vocab import Vocab

# English words will never exist in the real data. I'm taking
# advantage of that to allow the tests to expect things
# not to exist, or that make modifications to not rely on
# the existing data.


class MainTestCase(unittest.TestCase):

    def setUp(self):
        self.vocab = Vocab('vocab.csv')
        self.vocab.new('new')
        self.vocab.new('new2')
        self.vocab.new('new3')
        self.vocab.new_kana('new2', 'kana1')
        self.vocab.new_kana('new2', 'kana2')
        self.vocab.new_kana('new2', 'kana3')

    def replace_indices():
        return [
            ('new', ['n', '-50'], ['n', '-50']),
            ('new', ['n', '-1'], ['n', '-1']),
            ('new', ['n', '0'], ['n', '0']),
            ('new', ['n', '1'], ['n', 'new']),
            ('new', ['n', '2'], ['n', 'new2']),
            ('new', ['n', '3'], ['n', 'new3']),
            ('new', ['n', '4'], ['n', '4']),
            ('new', ['n', '999'], ['n', '999']),
            ('new', ['n', '1', '1'], ['n', 'new', '1']),
            ('new', ['n', '2', '-50'], ['n', 'new2', '-50']),
            ('new', ['n', '2', '-1'], ['n', 'new2', '-1']),
            ('new', ['n', '2', '0'], ['n', 'new2', '0']),
            ('new', ['n', '2', '1'], ['n', 'new2', 'kana1']),
            ('new', ['n', '2', '2'], ['n', 'new2', 'kana2']),
            ('new', ['n', '2', '3'], ['n', 'new2', 'kana3']),
            ('new', ['n', '2', '4'], ['n', 'new2', '4']),
            ('new', ['n', '2', '999'], ['n', 'new2', '999']),
        ]

    @data_provider(replace_indices)
    def test_replace_indices(self, search, params, expected_result):
        found_kanji = self.vocab.search(search)
        self.assertEqual(replace_indices(
            self.vocab, found_kanji, params), expected_result)
