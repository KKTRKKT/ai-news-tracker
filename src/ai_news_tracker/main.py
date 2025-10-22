# ai-news-tracker/src/ai_news_tracker/main.py

import logging
from .fetcher import fetch_news
from .parser import parse_articles
from .classifier import classify_articles
from .storage import store_articles
from .config import CONFIG

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting AI News Tracker...")

    # Fetch news articles
    articles = fetch_news(CONFIG['FEED_URLS'])
    logging.info(f"Fetched {len(articles)} articles.")

    # Parse the articles
    parsed_articles = parse_articles(articles)
    logging.info(f"Parsed {len(parsed_articles)} articles.")

    # Classify the articles
    classified_articles = classify_articles(parsed_articles)
    logging.info(f"Classified {len(classified_articles)} articles.")

    # Store the articles
    store_articles(classified_articles)
    logging.info("Stored articles successfully.")

if __name__ == "__main__":
    main()