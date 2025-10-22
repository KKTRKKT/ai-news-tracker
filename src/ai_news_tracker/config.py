# Configuration settings for the AI News Tracker application

class Config:
    # Feed URLs for news sources
    FEED_URLS = [
        "https://example.com/rss",
        "https://another-example.com/rss"
    ]
    
    # Slack webhook URL for notifications
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/your/webhook/url"
    
    # Database configuration
    DATABASE = {
        "host": "localhost",
        "port": 5432,
        "user": "your_username",
        "password": "your_password",
        "database": "ai_news_tracker_db"
    }
    
    # Logging configuration
    LOGGING = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }