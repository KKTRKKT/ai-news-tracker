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
SEND_MODE = os.getenv("SEND_MODE", "MULTIPLE")  # MULTIPLE | SINGLE
ITEMS_PER_MESSAGE = int(os.getenv("ITEMS_PER_MESSAGE", "10"))

# 대량 피드(arXiv 등)에서 피드당 가져오는 항목 수 제한
MAX_ITEMS_PER_FEED = int(os.getenv("MAX_ITEMS_PER_FEED", "30"))

# Gemini API 무료 티어 보호: 한 번에 처리할 최대 항목 수
MAX_GEMINI_ITEMS = int(os.getenv("MAX_GEMINI_ITEMS", "80"))

def load_feeds(path="feeds.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["feeds"]

def entry_id(e):
    # URL 우선, 없으면 title+published 해시
    key = e.get("link") or (e.get("title","") + "|" + e.get("published",""))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

def filter_by_date_range(entries):
    """날짜별 필터링
    - DAILY_SUMMARY: 어제 00:00 KST ~ 오늘 00:00 KST (정확히 전날 하루분)
    - HOURLY_CHECK:  오늘 00:00 KST ~ 현재
    """
    tz = pytz.timezone(TIMEZONE)
    now = now_kst()
    today_start = start_of_today_kst()

    if MODE == "DAILY_SUMMARY":
        # 정확히 "어제" 하루분만 가져옴
        yesterday_start = today_start - dt.timedelta(days=1)
        start = yesterday_start
        end = today_start
    else:
        # HOURLY_CHECK: 오늘 하루분
        start = today_start
        end = now

    print(f"[INFO] Date range: {start.strftime('%Y-%m-%d %H:%M')} ~ {end.strftime('%Y-%m-%d %H:%M')}")

    filtered = []
    no_date_count = 0

    for e in entries:
        pub_dt = e.get("published_dt")
        if not pub_dt:
            # 날짜 정보가 없는 경우:
            # DAILY_SUMMARY에서는 건너뜀 (날짜 불명확한 것은 제외)
            # HOURLY_CHECK에서는 포함 (빠진 날짜 차피 오늘 글로 간주)
            if MODE == "HOURLY_CHECK":
                no_date_count += 1
                filtered.append(e)
            continue

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

            # 피드당 최대 항목 수 제한 (arXiv 등 대량 피드 보호)
            entries_to_process = d.entries[:MAX_ITEMS_PER_FEED]
            if feed_items > MAX_ITEMS_PER_FEED:
                print(f"[INFO] Capped {f['name']}: {feed_items} → {MAX_ITEMS_PER_FEED} items")

            for raw in entries_to_process:
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
    뉴스 아이템 포맷팅 - 모든 항목 표시

    Args:
        items: 뉴스 아이템 리스트
        use_gemini_text: Gemini 요약/번역 텍스트 사용 여부
    """
    if not items:
        return "항목이 없습니다."

    lines = []
    for e in items:
        date_str = ""
        if e.get("published_dt"):
            date_str = e["published_dt"].strftime("%m/%d %H:%M")

        # Gemini 요약/번역 사용
        if use_gemini_text and e.get("summary_ko"):
            title_text = e["summary_ko"]
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

    return "\n\n".join(lines)

def send_with_mode(title, items, use_gemini_text):
    """
    SEND_MODE에 따라 Slack 메시지 전송 방식 결정
    - SINGLE: 전체를 하나의 메시지로 (항목이 적을 때)
    - MULTIPLE: 첫 N개 메시지 + 나머지를 분할 전송 (항목이 많을 때)
    """
    if not SLACK_WEBHOOK:
        print("[WARN] SLACK_WEBHOOK not configured - skipping notification")
        print("\n=== Preview ===")
        print(format_summary(items[:5], use_gemini_text))
        return

    if SEND_MODE == "SINGLE" or len(items) <= ITEMS_PER_MESSAGE:
        # SINGLE 모드 또는 항목이 적으면 하나의 메시지로 전송
        body = format_summary(items, use_gemini_text)
        print(f"[INFO] Sending single message ({len(items)} items)")
        send_slack(title, body)
        return

    # MULTIPLE 모드: 첫 메시지에 ITEMS_PER_MESSAGE건, 나머지를 10건씩 분할
    # 첫 메시지
    first_batch = items[:ITEMS_PER_MESSAGE]
    remaining = items[ITEMS_PER_MESSAGE:]
    chunk_size = 10  # 연속 메시지당 항목 수

    first_body = format_summary(first_batch, use_gemini_text)
    if remaining:
        total_pages = 1 + ((len(remaining) - 1) // chunk_size + 1)
        first_body += f"\n\n📄 ... 외 {len(remaining)}건 (다음 메시지에서 확인)"

    print(f"[INFO] Sending first message ({len(first_batch)} items, {len(remaining)} remaining)")
    send_slack(title, first_body)

    # 나머지 메시지를 분할 전송
    page = 1
    for i in range(0, len(remaining), chunk_size):
        chunk = remaining[i:i + chunk_size]
        total_pages = (len(remaining) - 1) // chunk_size + 1
        chunk_title = f"📄 계속 ({page}/{total_pages})"
        chunk_body = format_summary(chunk, use_gemini_text)
        print(f"[INFO] Sending continuation message {page}/{total_pages} ({len(chunk)} items)")
        send_slack(chunk_title, chunk_body)
        page += 1

def main():
    print(f"[INFO] ========================================")
    print(f"[INFO] Starting in {MODE} mode")
    print(f"[INFO] Current time (KST): {now_kst().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] Gemini API: {'Enabled' if USE_GEMINI and GEMINI_API_KEY else 'Disabled'}")
    print(f"[INFO] Send mode: {SEND_MODE} (first batch: {ITEMS_PER_MESSAGE}건)")
    print(f"[INFO] Max items per feed: {MAX_ITEMS_PER_FEED}")
    print(f"[INFO] Max Gemini items: {MAX_GEMINI_ITEMS}")
    print(f"[INFO] ========================================")

    all_items = fetch_all()

    if not all_items:
        print("[WARN] No items fetched from any feed!")
        return

    # 날짜별 필터링
    print(f"[INFO] Filtering items...")
    filtered_items = filter_by_date_range(all_items)
    print(f"[INFO] Items after date filtering: {len(filtered_items)}")

    seen = load_seen()
    print(f"[INFO] Previously seen items: {len(seen)}")

    if MODE == "DAILY_SUMMARY":
        # seen에 오늘 날짜 기준으로 저장하되, 어제의 뉴스를 요약 전송
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

            # Gemini API로 요약/번역 (MAX_GEMINI_ITEMS 이하로 제한)
            use_gemini_text = False
            if USE_GEMINI and GEMINI_API_KEY:
                try:
                    items_for_gemini = sorted_items[:MAX_GEMINI_ITEMS]
                    skipped = len(sorted_items) - len(items_for_gemini)
                    if skipped > 0:
                        print(f"[INFO] Gemini will process {len(items_for_gemini)} items (skipping {skipped} to stay under limit)")

                    print(f"[INFO] Processing with Gemini API...")
                    summarizer = GeminiSummarizer(GEMINI_API_KEY)
                    summarized = summarizer.batch_summarize(items_for_gemini, delay=1.0)
                    use_gemini_text = True
                    print(f"[INFO] Gemini processing completed for {len(summarized)} items")

                    # 처리된 것과 미처리 것을 다시 합침
                    sorted_items = summarized + sorted_items[MAX_GEMINI_ITEMS:]
                except Exception as e:
                    print(f"[ERROR] Gemini API 오류: {e}")
                    print(f"[INFO] Falling back to original format")

            if SLACK_WEBHOOK:
                yesterday = (now_kst() - dt.timedelta(days=1)).strftime('%Y-%m-%d')
                title = f"📌 {yesterday} AI 뉴스 요약 ({len(filtered_items)}건)"
                if use_gemini_text:
                    title += " 🤖"
                print(f"[INFO] Sending Slack notification (mode: {SEND_MODE})")
                send_with_mode(title, sorted_items, use_gemini_text)
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

            # Gemini API로 요약/번역 (MAX_GEMINI_ITEMS 이하로 제한)
            use_gemini_text = False
            if USE_GEMINI and GEMINI_API_KEY:
                try:
                    items_for_gemini = sorted_items[:MAX_GEMINI_ITEMS]
                    skipped = len(sorted_items) - len(items_for_gemini)
                    if skipped > 0:
                        print(f"[INFO] Gemini will process {len(items_for_gemini)} items (skipping {skipped})")

                    print(f"[INFO] Processing with Gemini API...")
                    summarizer = GeminiSummarizer(GEMINI_API_KEY)
                    summarized = summarizer.batch_summarize(items_for_gemini, delay=1.0)
                    use_gemini_text = True
                    print(f"[INFO] Gemini processing completed for {len(summarized)} items")

                    sorted_items = summarized + sorted_items[MAX_GEMINI_ITEMS:]
                except Exception as e:
                    print(f"[ERROR] Gemini API 오류: {e}")
                    print(f"[INFO] Falling back to original format")

            if SLACK_WEBHOOK:
                title = f"🆕 신규 감지 {now_kst().strftime('%H:%M KST')} ({len(new_items)}건)"
                if use_gemini_text:
                    title += " 🤖"
                print(f"[INFO] Sending Slack notification (mode: {SEND_MODE})")
                send_with_mode(title, sorted_items, use_gemini_text)

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
