import unittest
from scripts.archive_record_guard import assert_record_delimiters, missing_record_delimiters


class ArchiveRecordGuardTests(unittest.TestCase):
    def test_valid_two_records(self):
        text = '# Inbox\n\n---\nid: MSG-1\nfrom: grok\n---\n\nintent: ok\n\n---\nid: MSG-2\nfrom: grok\n---\n'
        self.assertEqual(missing_record_delimiters(text), [])
        assert_record_delimiters(text, 'messages/test.md')

    def test_missing_opening_delimiter(self):
        text = '# Inbox\n\n---\nid: MSG-1\n---\n\nintent: ok\n\nid: MSG-2\n'
        self.assertEqual(missing_record_delimiters(text), [9])
        with self.assertRaisesRegex(ValueError, 'missing record delimiter'):
            assert_record_delimiters(text, 'messages/test.md')

    def test_first_line_id_without_delimiter(self):
        self.assertEqual(missing_record_delimiters('id: MSG-1\n'), [1])

    def test_non_record_mentions_not_flagged(self):
        self.assertEqual(missing_record_delimiters('text mentions id: MSG-1\n'), [])


if __name__ == '__main__':
    unittest.main()
