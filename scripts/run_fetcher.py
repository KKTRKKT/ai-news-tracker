import sys
from src.ai_news_tracker.fetcher import fetch_news

def main():
    try:
        articles = fetch_news()
        for article in articles:
            print(f"Title: {article['title']}, Link: {article['link']}, Date: {article['date']}")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()