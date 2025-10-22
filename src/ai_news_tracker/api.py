from flask import Flask, jsonify, request
from .storage import Storage
from .fetcher import fetch_articles
from .parser import parse_articles
from .classifier import classify_articles

app = Flask(__name__)
storage = Storage()

@app.route('/articles', methods=['GET'])
def get_articles():
    articles = storage.get_all_articles()
    return jsonify(articles)

@app.route('/fetch', methods=['POST'])
def fetch_and_store_articles():
    sources = request.json.get('sources', [])
    fetched_articles = fetch_articles(sources)
    parsed_articles = parse_articles(fetched_articles)
    classified_articles = classify_articles(parsed_articles)
    storage.save_articles(classified_articles)
    return jsonify({'message': 'Articles fetched and stored successfully.'}), 201

if __name__ == '__main__':
    app.run(debug=True)