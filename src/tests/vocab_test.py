import contextlib
import io
import unittest
from unittest_data_provider import data_provider
from vocab import Vocab

# English words will never exist in the real data. I'm taking
# advantage of that, and that 送る has one reading, to allow
# the tests to expect things not to exist, or that make
# modifications to not rely on the existing data.


class VocabTestCase(unittest.TestCase):

    def setUp(self):
        self.vocab = Vocab('vocab.csv')

    def test_contains(self):
        self.assertTrue(self.vocab.contains('送る'))
        self.assertTrue(self.vocab.contains('送る', 'おくる'))
        self.assertTrue(not self.vocab.contains('junk'))
        self.assertTrue(not self.vocab.contains('送る', 'junk'))

    def test_kanji(self):
        self.assertTrue(not self.vocab.contains('new'))
        list_name = self.vocab.new('new')
        self.assertEqual(self.vocab.get_list_name('new'), list_name)
        self.assertEqual(self.vocab.get_known('new'), False)
        self.assertEqual(self.vocab.toggle_known('new'), True)
        self.assertEqual(self.vocab.get_known('new'), True)
        self.assertEqual(self.vocab.toggle_known('new'), False)
        self.assertEqual(self.vocab.get_known('new'), False)
        self.assertTrue(self.vocab.contains('new'))
        self.assertEqual(self.vocab.delete('new'), list_name)

    def test_kana(self):
        self.assertTrue(not self.vocab.contains('送る', 'new'))
        index = self.vocab.new_kana('送る', 'new')
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new'])
        index2 = self.vocab.new_kana('送る', 'new2')
        self.assertTrue(self.vocab.contains('送る', 'new2'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new', 'new2'])
        self.assertEqual(self.vocab.delete_kana('送る', 'new2'), index2)
        self.assertTrue(not self.vocab.contains('送る', 'new2'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new'])
        index2 = self.vocab.new_kana('送る', 'new2')
        self.assertEqual(self.vocab.delete_kana('送る', 'new'), index)
        self.assertTrue(not self.vocab.contains('送る', 'new'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new2'])
        self.assertEqual(self.vocab.delete_kana('送る', 'new2'), index)
        self.assertTrue(not self.vocab.contains('送る', 'new2'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる'])

    def bad_files_provider():
        return [
            (
                'vocab_bad_kana.csv',
                "line 3: bad kana list ',,'"),
            (
                'vocab_bad_kanji.csv',
                "line 3: empty kanji ''."
            ),
            (
                'vocab_bad_line.csv',
                "line 3: bad line '0100,送る', 2 fields, expected at least 4."
            ),
            (
                'vocab_bad_list_name.csv',
                "line 3: bad list name 'asdd', expected numeric."
            )
        ]

    @data_provider(bad_files_provider)
    def test_bad_files(self, filename, expectedError):
        with self.assertRaises(Exception) as context:
            Vocab(f'src/tests/test_data/{filename}')
        self.assertIn(expectedError, str(context.exception))
