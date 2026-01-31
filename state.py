import os, json, datetime as dt
from utils import now_kst, start_of_today_kst

def _path(date_str=None):
    """날짜별 seen 파일 경로 반환"""
    if date_str is None:
        date_str = now_kst().strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)
    return f"data/seen-{date_str}.json"

def _load_file(path):
    """단일 seen 파일을 읽어 set으로 반환"""
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            arr = json.load(f)
            return set(arr)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[WARN] Failed to load seen file {path}: {e}")
        return set()

def load_seen():
    """
    오늘과 어제의 seen 파일을 모두 읽어서 합친다.
    
    이유: seen 파일이 날짜별로 저장되는데, HOURLY_CHECK가 자정 직후에 실행되면
    어제의 seen 파일만 있고 오늘의 파일은 없다. 이 경우 어제 이미 본 항목이
    오늘 다시 "신규"로 보여질 수 있다. 어제 파일을 포함하여 이를 방지한다.
    """
    today = now_kst().strftime("%Y-%m-%d")
    yesterday = (now_kst() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

    today_seen = _load_file(_path(today))
    yesterday_seen = _load_file(_path(yesterday))

    merged = today_seen | yesterday_seen

    if yesterday_seen:
        print(f"[INFO] Loaded seen: today={len(today_seen)}, yesterday={len(yesterday_seen)}, merged={len(merged)}")
    else:
        print(f"[INFO] Loaded seen: {len(today_seen)} items (today only)")

    return merged

def save_seen(seen):
    """오늘 날짜의 seen 파일에 저장"""
    p = _path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)