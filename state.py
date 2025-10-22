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
