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
    """당일 00:00~현재(KST) 범위의 게시물만 필터링"""
    tz = pytz.timezone(TIMEZONE)
    start = start_of_today_kst()
    end = now_kst()
    
    filtered = []
    for e in entries:
        # published_dt가 이미 normalize_entry에서 처리됨
        pub_dt = e.get("published_dt")
        if not pub_dt:
            # 날짜 정보가 없는 경우 최근 항목으로 간주하고 포함
            print(f"[DEBUG] No date for: {e.get('title')[:50]}")
            filtered.append(e)
            continue
        
        # KST로 변환 (이미 되어있을 수도 있음)
        if pub_dt.tzinfo is None:
            pub_dt = tz.localize(pub_dt)
        else:
            pub_dt = pub_dt.astimezone(tz)
        
        if start <= pub_dt <= end:
            filtered.append(e)
            print(f"[DEBUG] Include: {pub_dt.strftime('%Y-%m-%d %H:%M')} - {e.get('title')[:50]}")
        else:
            print(f"[DEBUG] Exclude: {pub_dt.strftime('%Y-%m-%d %H:%M')} - {e.get('title')[:50]}")
    
    return filtered

def fetch_all():
    feeds = load_feeds()
    items = []
    for f in feeds:
        print(f"[DEBUG] Fetching: {f['name']}")
        try:
            d = feedparser.parse(f["url"])
            print(f"[DEBUG] Found {len(d.entries)} entries from {f['name']}")
            for raw in d.entries:
                e = normalize_entry(raw, f["name"])
                e["__id"] = entry_id(e)
                items.append(e)
        except Exception as ex:
            print(f"[ERROR] Failed to fetch {f['name']}: {ex}")
    
    print(f"[DEBUG] Total items fetched: {len(items)}")
    return items

def format_summary(items):
    lines = []
    # 상위 20개 제한 (스팸 방지)
    for e in items[:20]:
        line = f"• [{e.get('source')}] {e.get('title')} — {e.get('link')}"
        lines.append(line)
    if len(items) > 20:
        lines.append(f"\n... 외 {len(items) - 20}개 항목")
    return "\n".join(lines)

def main():
    print(f"[INFO] Starting in {MODE} mode")
    print(f"[INFO] Current time (KST): {now_kst().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_items = fetch_all()
    print(f"[INFO] Filtering for today's items...")
    today_items = filter_today(all_items)
    print(f"[INFO] Today's items: {len(today_items)}")
    
    seen = load_seen()
    print(f"[INFO] Previously seen items: {len(seen)}")

    if MODE == "DAILY_SUMMARY":
        # 초기화: 오늘 분에 해당하는 항목을 seen에 기록하고 요약 발송
        print(f"[INFO] Adding {len(today_items)} items to seen set")
        for e in today_items:
            seen.add(e["__id"])
        save_seen(seen)
        
        if SLACK_WEBHOOK and today_items:
            title = f"📌 {now_kst().strftime('%Y-%m-%d')} AI 뉴스 요약 (09:00 KST)"
            body = format_summary(sorted(today_items, key=lambda x: x.get("published_dt") or now_kst(), reverse=True))
            print(f"[INFO] Sending Slack notification with {len(today_items)} items")
            send_slack(title, body)
        elif not SLACK_WEBHOOK:
            print("[WARN] SLACK_WEBHOOK not configured")
        elif not today_items:
            print("[INFO] No items to report")
        return

    if MODE == "HOURLY_CHECK":
        new_items = [e for e in today_items if e["__id"] not in seen]
        print(f"[INFO] New items found: {len(new_items)}")
        
        if new_items and SLACK_WEBHOOK:
            title = f"🆕 신규 감지 {now_kst().strftime('%H:%M KST')} ({len(new_items)}건)"
            body = format_summary(sorted(new_items, key=lambda x: x.get("published_dt") or now_kst(), reverse=True))
            send_slack(title, body)
        
        # 신규는 seen에 병합 저장
        if new_items:
            for e in new_items:
                seen.add(e["__id"])
            save_seen(seen)
            print(f"[INFO] Saved {len(new_items)} new items to seen set")
        return

if __name__ == "__main__":
    main()
