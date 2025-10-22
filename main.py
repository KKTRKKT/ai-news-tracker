import os, json, hashlib, sys, datetime as dt
from dateutil import parser as dp
import pytz, feedparser, yaml
from utils import normalize_entry, now_kst, start_of_today_kst
from state import load_seen, save_seen
from notifier import send_slack

TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
MODE = os.getenv("MODE", "DAILY_SUMMARY")  # DAILY_SUMMARY | HOURLY_CHECK
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

def load_feeds(path="feeds.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["feeds"]

def entry_id(e):
    # URL 우선, 없으면 title+published 해시
    key = e.get("link") or (e.get("title","") + "|" + e.get("published",""))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

def filter_today(entries):
    # 당일 00:00~현재(KST) 범위의 게시물만
    tz = pytz.timezone(TIMEZONE)
    start = start_of_today_kst()
    end = now_kst()
    def _in_today(e):
        ts = e.get("published_parsed")
        if not ts:
            return True  # 시간 없는 피드는 일단 통과
        t = dt.datetime.fromtimestamp(dt.datetime(*ts[:6]).timestamp(), tz)
        return start <= t <= end
    return [e for e in entries if _in_today(e)]

def fetch_all():
    feeds = load_feeds()
    items = []
    for f in feeds:
        d = feedparser.parse(f["url"])
        for raw in d.entries:
            e = normalize_entry(raw, f["name"])
            e["__id"] = entry_id(e)
            items.append(e)
    return items

def format_summary(items):
    lines = []
    # 상위 20개 제한 (스팸 방지)
    for e in items[:20]:
        line = f"• [{e.get('source')}] {e.get('title')} — {e.get('link')}"
        lines.append(line)
    return "\n".join(lines)

def main():
    all_items = fetch_all()
    today_items = filter_today(all_items)
    seen = load_seen()

    if MODE == "DAILY_SUMMARY":
        # 초기화: 오늘 분에 해당하는 항목을 seen에 기록하고 요약 발송
        for e in today_items:
            seen.add(e["__id"])
        save_seen(seen)
        if SLACK_WEBHOOK:
            title = f"📌 {now_kst().strftime('%Y-%m-%d')} AI 뉴스 요약 (09:00 KST)"
            body = format_summary(sorted(today_items, key=lambda x: x.get("published_dt") or now_kst(), reverse=True))
            send_slack(title, body)
        return

    if MODE == "HOURLY_CHECK":
        new_items = [e for e in today_items if e["__id"] not in seen]
        if new_items and SLACK_WEBHOOK:
            title = f"🆕 신규 감지 {now_kst().strftime('%H:%M KST')} ({len(new_items)}건)"
            body = format_summary(sorted(new_items, key=lambda x: x.get("published_dt") or now_kst(), reverse=True))
            send_slack(title, body)
        # 신규는 seen에 병합 저장
        for e in new_items:
            seen.add(e["__id"])
        save_seen(seen)
        return

if __name__ == "__main__":
    main()

utils.py

import datetime as dt
from dateutil import parser as dp
import pytz

TZ = pytz.timezone("Asia/Seoul")

def now_kst():
    return dt.datetime.now(TZ)

def start_of_today_kst():
    n = now_kst()
    return TZ.localize(dt.datetime(n.year, n.month, n.day, 0, 0, 0))

def normalize_entry(raw, source_name):
    # 공통 필드 정규화
    title = getattr(raw, "title", "").strip()
    link = getattr(raw, "link", "").strip()
    published = getattr(raw, "published", None)
    published_dt = None
    if published:
        try:
            published_dt = dp.parse(published)
            if not published_dt.tzinfo:
                published_dt = TZ.localize(published_dt)
            else:
                published_dt = published_dt.astimezone(TZ)
        except Exception:
            published_dt = None
    e = {
        "source": source_name,
        "title": title,
        "link": link,
        "published": published,
        "published_dt": published_dt,
        "published_parsed": getattr(raw, "published_parsed", None)
    }
    return e

state.py

GitHub Actions가 저장소에 커밋하여 상태를 영속화합니다.

import os, json, datetime as dt
from utils import now_kst, start_of_today_kst

def _path():
    today = now_kst().strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)
    return f"data/seen-{today}.json"

def load_seen():
    p = _path()
    if not os.path.exists(p):
        return set()
    with open(p, "r", encoding="utf-8") as f:
        arr = json.load(f)
        return set(arr)

def save_seen(seen):
    p = _path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)

notifier.py (Slack)

import os, requests

def send_slack(title, body):
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        return
    text = f"*{title}*\n{body}"
    requests.post(webhook, json={"text": text}, timeout=10)