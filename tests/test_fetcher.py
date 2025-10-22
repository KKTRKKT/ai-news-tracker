import unittest
from ai_news_tracker.fetcher import fetch_articles

class TestFetcher(unittest.TestCase):

    def test_fetch_articles_valid_source(self):
        # Test fetching articles from a valid source
        source = "https://example.com/rss"
        articles = fetch_articles(source)
        self.assertIsInstance(articles, list)
        self.assertGreater(len(articles), 0)

    def test_fetch_articles_invalid_source(self):
        # Test fetching articles from an invalid source
        source = "https://invalid-url.com/rss"
        with self.assertRaises(Exception):
            fetch_articles(source)

    def test_fetch_articles_empty_source(self):
        # Test fetching articles from an empty source
        source = ""
        with self.assertRaises(ValueError):
            fetch_articles(source)

if __name__ == '__main__':
    unittest.main()