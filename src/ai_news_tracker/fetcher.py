import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def fetch_rss_feed(url: str) -> List[Dict[str, str]]:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    soup = BeautifulSoup(response.content, features='xml')
    
    articles = []
    for item in soup.findAll('item'):
        article = {
            'title': item.title.text,
            'link': item.link.text,
            'pub_date': item.pubDate.text
        }
        articles.append(article)
    
    return articles

def fetch_news(sources: List[str]) -> List[Dict[str, str]]:
    all_articles = []
    for source in sources:
        try:
            articles = fetch_rss_feed(source)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Failed to fetch from {source}: {e}")
    
    return all_articles