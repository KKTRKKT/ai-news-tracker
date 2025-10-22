def parse_article(article):
    """
    Parses a single news article and extracts relevant information.

    Args:
        article (dict): A dictionary containing the raw article data.

    Returns:
        dict: A dictionary containing the parsed article information, including title, link, and publication date.
    """
    parsed_data = {
        'title': article.get('title'),
        'link': article.get('link'),
        'published_date': article.get('published_date'),
    }
    return parsed_data


def parse_articles(articles):
    """
    Parses a list of news articles.

    Args:
        articles (list): A list of dictionaries containing raw article data.

    Returns:
        list: A list of dictionaries containing parsed article information.
    """
    return [parse_article(article) for article in articles]