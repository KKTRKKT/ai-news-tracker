import os, requests

def send_slack(title, body):
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        return
    text = f"*{title}*\n{body}"
    requests.post(webhook, json={"text": text}, timeout=10)