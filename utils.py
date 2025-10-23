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
    """공통 필드 정규화 - 타임존 처리 개선"""
    title = getattr(raw, "title", "").strip()
    link = getattr(raw, "link", "").strip()
    published = getattr(raw, "published", None)
    published_dt = None
    
    if published:
        try:
            # dateutil.parser로 파싱
            published_dt = dp.parse(published)
            
            # UTC로 간주하고 KST로 변환 (대부분의 RSS는 UTC 또는 명시적 timezone)
            if published_dt.tzinfo is None:
                # timezone 정보가 없으면 UTC로 간주
                published_dt = pytz.UTC.localize(published_dt)
            
            # KST로 변환
            published_dt = published_dt.astimezone(TZ)
            
        except Exception as e:
            print(f"[WARN] Failed to parse date '{published}': {e}")
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
