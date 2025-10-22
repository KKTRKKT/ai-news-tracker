# AI News Tracker

## Overview
The AI News Tracker is a Python-based application designed to fetch, parse, classify, and store news articles from various sources. It aims to provide users with a streamlined way to stay updated on the latest news in their areas of interest.

## Project Structure
```
ai-news-tracker
├── src
│   └── ai_news_tracker
│       ├── __init__.py
│       ├── main.py
│       ├── fetcher.py
│       ├── parser.py
│       ├── classifier.py
│       ├── storage.py
│       ├── db.py
│       ├── api.py
│       ├── config.py
│       └── utils.py
├── scripts
│   └── run_fetcher.py
├── tests
│   ├── test_fetcher.py
│   ├── test_parser.py
│   └── test_classifier.py
├── .github
│   └── workflows
│       ├── ci.yml
│       └── scheduled_fetch.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Features
- **Fetching**: Automatically retrieves news articles from various sources using RSS/Atom feeds.
- **Parsing**: Extracts relevant information such as titles, links, and publication dates from the fetched articles.
- **Classification**: Classifies articles based on predefined categories or keywords.
- **Storage**: Saves processed articles to JSON files or a database for easy access.
- **API**: Exposes an API for accessing stored articles and triggering fetch operations.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-news-tracker.git
   cd ai-news-tracker
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application, execute the following command:
```
python src/ai_news_tracker/main.py
```

You can also run the fetcher module independently using:
```
python scripts/run_fetcher.py
```

## Testing
To run the tests, use:
```
pytest tests/
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.