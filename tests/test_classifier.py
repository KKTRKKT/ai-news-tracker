import unittest
from src.ai_news_tracker.classifier import classify_article

class TestClassifier(unittest.TestCase):

    def test_classify_article_positive(self):
        article = {
            'title': 'AI is transforming the world',
            'content': 'Artificial Intelligence is making significant impacts in various sectors.'
        }
        expected_category = 'Technology'
        self.assertEqual(classify_article(article), expected_category)

    def test_classify_article_negative(self):
        article = {
            'title': 'Cooking tips for beginners',
            'content': 'Learn how to cook delicious meals easily.'
        }
        expected_category = 'Lifestyle'
        self.assertEqual(classify_article(article), expected_category)

    def test_classify_article_empty(self):
        article = {}
        expected_category = 'Uncategorized'
        self.assertEqual(classify_article(article), expected_category)

if __name__ == '__main__':
    unittest.main()