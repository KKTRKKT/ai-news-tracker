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
