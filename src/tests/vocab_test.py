import contextlib
import io
import unittest
from unittest_data_provider import data_provider
from vocab import Vocab


class VocabTestCase(unittest.TestCase):

    def setUp(self):
        self.vocab = Vocab('src/tests/test_data/vocab_good.csv')

    def test_contains(self):
        self.assertTrue(self.vocab.contains('送る'))
        self.assertTrue(self.vocab.contains('送る', 'おくる'))
        self.assertFalse(self.vocab.contains('junk'))
        self.assertFalse(self.vocab.contains('送る', 'junk'))

    def test_add_delete_kanji(self):
        self.assertFalse(self.vocab.contains('new'))
        list_name = self.vocab.add('new')
        self.assertEqual(self.vocab.get_list_name('new'), list_name)
        self.assertEqual(self.vocab.get_known('new'), False)
        self.assertEqual(self.vocab.toggle_known('new'), True)
        self.assertEqual(self.vocab.get_known('new'), True)
        self.assertEqual(self.vocab.toggle_known('new'), False)
        self.assertEqual(self.vocab.get_known('new'), False)
        self.assertTrue(self.vocab.contains('new'))
        self.assertEqual(self.vocab.delete('new'), list_name)

    def test_change_kanji(self):
        self.assertFalse(self.vocab.contains('new'))
        list_name = self.vocab.add('new')
        self.vocab.add_kana('new', 'kana')
        self.vocab.add_kana('new', 'kana2')
        self.assertTrue(self.vocab.contains('new'))
        self.assertTrue(self.vocab.contains('new', 'kana'))
        self.assertTrue(self.vocab.contains('new', 'kana2'))
        self.assertFalse(self.vocab.contains('NEW'))
        self.assertFalse(self.vocab.contains('NEW', 'kana'))
        self.assertFalse(self.vocab.contains('NEW', 'kana2'))
        self.vocab.change('new', 'NEW')
        self.assertFalse(self.vocab.contains('new'))
        self.assertFalse(self.vocab.contains('new', 'kana'))
        self.assertFalse(self.vocab.contains('new', 'kana2'))
        self.assertTrue(self.vocab.contains('NEW'))
        self.assertTrue(self.vocab.contains('NEW', 'kana'))
        self.assertTrue(self.vocab.contains('NEW', 'kana2'))

    def test_add_delete_kana(self):
        self.assertFalse(self.vocab.contains('送る', 'new'))
        index = self.vocab.add_kana('送る', 'new')
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new'])
        index2 = self.vocab.add_kana('送る', 'new2')
        self.assertTrue(self.vocab.contains('送る', 'new2'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new', 'new2'])
        self.assertEqual(self.vocab.delete_kana('送る', 'new2'), index2)
        self.assertFalse(self.vocab.contains('送る', 'new2'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new'])
        index2 = self.vocab.add_kana('送る', 'new2')
        self.assertEqual(self.vocab.delete_kana('送る', 'new'), index)
        self.assertFalse(self.vocab.contains('送る', 'new'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる', 'new2'])
        self.assertEqual(self.vocab.delete_kana('送る', 'new2'), index)
        self.assertFalse(self.vocab.contains('送る', 'new2'))
        self.assertEqual(self.vocab.get_kana('送る'), ['おくる'])

    def test_change_kana(self):
        self.assertFalse(self.vocab.contains('new'))
        list_name = self.vocab.add('new')
        self.vocab.add_kana('new', 'kana')
        self.vocab.add_kana('new', 'kana2')
        self.assertTrue(self.vocab.contains('new'))
        self.assertTrue(self.vocab.contains('new', 'kana'))
        self.assertTrue(self.vocab.contains('new', 'kana2'))
        self.assertFalse(self.vocab.contains('new', 'kana3'))
        self.assertEqual(['kana', 'kana2'], self.vocab.get_kana('new'))
        self.vocab.change_kana('new', 'kana', 'kana3')
        self.assertTrue(self.vocab.contains('new'))
        self.assertFalse(self.vocab.contains('new', 'kana'))
        self.assertTrue(self.vocab.contains('new', 'kana2'))
        self.assertTrue(self.vocab.contains('new', 'kana3'))
        self.assertEqual(['kana3', 'kana2'], self.vocab.get_kana('new'))

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
