import unittest
from ai_news_tracker.parser import parse_article

class TestParser(unittest.TestCase):

    def test_parse_article_valid(self):
        raw_article = {
            'title': 'Sample News Title',
            'link': 'http://example.com/sample-news',
            'pub_date': '2023-10-01T12:00:00Z',
            'content': 'This is a sample news article content.'
        }
        expected_output = {
            'title': 'Sample News Title',
            'link': 'http://example.com/sample-news',
            'pub_date': '2023-10-01T12:00:00Z',
            'content': 'This is a sample news article content.'
        }
        parsed_article = parse_article(raw_article)
        self.assertEqual(parsed_article, expected_output)

    def test_parse_article_missing_fields(self):
        raw_article = {
            'title': 'Sample News Title',
            'link': 'http://example.com/sample-news'
        }
        with self.assertRaises(KeyError):
            parse_article(raw_article)

if __name__ == '__main__':
    unittest.main()