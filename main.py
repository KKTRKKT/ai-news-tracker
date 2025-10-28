import os, json, hashlib, sys, datetime as dt
from dateutil import parser as dp
import pytz, feedparser, yaml
from utils import normalize_entry, now_kst, start_of_today_kst
from state import load_seen, save_seen
from notifier import send_slack
from gemini_summarizer import GeminiSummarizer

TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul")
MODE = os.getenv("MODE", "DAILY_SUMMARY")  # DAILY_SUMMARY | HOURLY_CHECK
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() == "true"

def load_feeds(path="feeds.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["feeds"]

def entry_id(e):
    # URL 우선, 없으면 title+published 해시
    key = e.get("link") or (e.get("title","") + "|" + e.get("published",""))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

def filter_by_date_range(entries, days_back=7):
    """최근 N일간의 게시물 필터링 (기본: 최근 7일)"""
    tz = pytz.timezone(TIMEZONE)
    now = now_kst()
    
    # DAILY_SUMMARY: 최근 7일 (충분히 넓게)
    # HOURLY_CHECK: 오늘 00:00 ~ 현재
    if MODE == "DAILY_SUMMARY":
        # 최근 N일 데이터 (더 넓게)
        start = now - dt.timedelta(days=days_back)
        end = now
    else:
        # 오늘 데이터
        start = start_of_today_kst()
        end = now
    
    print(f"[INFO] Date range: {start.strftime('%Y-%m-%d %H:%M')} ~ {end.strftime('%Y-%m-%d %H:%M')}")
    
    filtered = []
    no_date_count = 0
    
    for e in entries:
        pub_dt = e.get("published_dt")
        if not pub_dt:
            # 날짜 정보가 없는 경우 최근 항목으로 간주
            no_date_count += 1
            filtered.append(e)
            continue
        
        # 이미 KST로 변환되어 있음 (utils.py에서 처리)
        if start <= pub_dt <= end:
            filtered.append(e)
    
    print(f"[INFO] Filtered: {len(filtered)} items ({no_date_count} without date)")
    return filtered

def fetch_all():
    feeds = load_feeds()
    items = []
    for f in feeds:
        print(f"[DEBUG] Fetching: {f['name']}")
        try:
            d = feedparser.parse(f["url"])
            feed_items = len(d.entries)
            print(f"[DEBUG] Found {feed_items} entries from {f['name']}")
            
            for raw in d.entries:
                e = normalize_entry(raw, f["name"])
                e["__id"] = entry_id(e)
                
                # RSS 초록 추출 (summary 또는 description)
                summary = getattr(raw, "summary", "") or getattr(raw, "description", "")
                e["summary"] = summary.strip() if summary else ""
                
                items.append(e)
        except Exception as ex:
            print(f"[ERROR] Failed to fetch {f['name']}: {ex}")
    
    print(f"[DEBUG] Total items fetched: {len(items)}")
    return items

def format_summary(items, use_gemini_text=False):
    """
    뉴스 아이템 포맷팅
    
    Args:
        items: 뉴스 아이템 리스트
        use_gemini_text: Gemini 요약/번역 텍스트 사용 여부
    """
    if not items:
        return "항목이 없습니다."
    
    lines = []
    # 상위 30개 제한
    for e in items[:30]:
        date_str = ""
        if e.get("published_dt"):
            date_str = e["published_dt"].strftime("%m/%d %H:%M")
        
        # Gemini 요약/번역 사용
        if use_gemini_text and e.get("summary_ko"):
            title_text = e["summary_ko"]
            # 초록이 있었는지 표시
            if e.get("has_summary"):
                prefix = "📝"  # 요약된 경우
            else:
                prefix = "🔤"  # 번역만 된 경우
        else:
            title_text = e.get("title")
            prefix = "•"
        
        line = f"{prefix} [{e.get('source')}] {title_text}"
        if date_str:
            line += f" ({date_str})"
        line += f"\n  {e.get('link')}"
        lines.append(line)
    
    if len(items) > 30:
        lines.append(f"\n... 외 {len(items) - 30}개 항목")
    
    return "\n\n".join(lines)

def main():
    print(f"[INFO] ========================================")
    print(f"[INFO] Starting in {MODE} mode")
    print(f"[INFO] Current time (KST): {now_kst().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] Gemini API: {'Enabled' if USE_GEMINI and GEMINI_API_KEY else 'Disabled'}")
    print(f"[INFO] ========================================")
    
    all_items = fetch_all()
    
    if not all_items:
        print("[WARN] No items fetched from any feed!")
        return
    
    # 날짜별 필터링
    print(f"[INFO] Filtering items...")
    filtered_items = filter_by_date_range(all_items)
    print(f"[INFO] Items after filtering: {len(filtered_items)}")
    
    seen = load_seen()
    print(f"[INFO] Previously seen items: {len(seen)}")

    if MODE == "DAILY_SUMMARY":
        # 전날 데이터를 seen에 기록하고 요약 발송
        print(f"[INFO] Processing {len(filtered_items)} items for daily summary")
        
        for e in filtered_items:
            seen.add(e["__id"])
        
        save_seen(seen)
        print(f"[INFO] Saved {len(seen)} items to seen set")
        
        if filtered_items:
            sorted_items = sorted(
                filtered_items, 
                key=lambda x: x.get("published_dt") or dt.datetime(1900, 1, 1, tzinfo=pytz.timezone(TIMEZONE)), 
                reverse=True
            )
            
            # Gemini API로 요약/번역
            use_gemini_text = False
            if USE_GEMINI and GEMINI_API_KEY:
                try:
                    print(f"[INFO] Processing with Gemini API...")
                    summarizer = GeminiSummarizer(GEMINI_API_KEY)
                    sorted_items = summarizer.batch_summarize(sorted_items, delay=1.0)
                    use_gemini_text = True
                    print(f"[INFO] Gemini processing completed")
                except Exception as e:
                    print(f"[ERROR] Gemini API 오류: {e}")
                    print(f"[INFO] Falling back to original format")
            
            if SLACK_WEBHOOK:
                yesterday = (now_kst() - dt.timedelta(days=1)).strftime('%Y-%m-%d')
                title = f"📌 {yesterday} AI 뉴스 요약 ({len(filtered_items)}건)"
                if use_gemini_text:
                    title += " 🤖"
                body = format_summary(sorted_items, use_gemini_text)
                print(f"[INFO] Sending Slack notification")
                send_slack(title, body)
            else:
                print("[WARN] SLACK_WEBHOOK not configured - skipping notification")
                print("\n=== Preview ===")
                print(format_summary(sorted_items[:5], use_gemini_text))
        else:
            print("[INFO] No items to report for daily summary")
        
        return

    if MODE == "HOURLY_CHECK":
        new_items = [e for e in filtered_items if e["__id"] not in seen]
        print(f"[INFO] New items found: {len(new_items)}")
        
        if new_items:
            sorted_items = sorted(
                new_items,
                key=lambda x: x.get("published_dt") or dt.datetime(1900, 1, 1, tzinfo=pytz.timezone(TIMEZONE)),
                reverse=True
            )
            
            # Gemini API로 요약/번역
            use_gemini_text = False
            if USE_GEMINI and GEMINI_API_KEY:
                try:
                    print(f"[INFO] Processing with Gemini API...")
                    summarizer = GeminiSummarizer(GEMINI_API_KEY)
                    sorted_items = summarizer.batch_summarize(sorted_items, delay=1.0)
                    use_gemini_text = True
                    print(f"[INFO] Gemini processing completed")
                except Exception as e:
                    print(f"[ERROR] Gemini API 오류: {e}")
                    print(f"[INFO] Falling back to original format")
            
            if SLACK_WEBHOOK:
                title = f"🆕 신규 감지 {now_kst().strftime('%H:%M KST')} ({len(new_items)}건)"
                if use_gemini_text:
                    title += " 🤖"
                body = format_summary(sorted_items, use_gemini_text)
                send_slack(title, body)
            
            # seen에 추가
            for e in new_items:
                seen.add(e["__id"])
            save_seen(seen)
            print(f"[INFO] Saved {len(new_items)} new items to seen set")
        else:
            print("[INFO] No new items found")
        
        return

if __name__ == "__main__":
    main()