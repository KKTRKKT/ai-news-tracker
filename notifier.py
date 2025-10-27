import os
import requests
import time

def send_slack(title, body):
    """
    Slack 메인 메시지 전송
    
    Returns:
        str: thread timestamp (thread 응답용) 또는 None
    """
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        print("[WARN] SLACK_WEBHOOK not configured")
        return None
    
    text = f"*{title}*\n{body}"
    
    try:
        response = requests.post(
            webhook, 
            json={"text": text}, 
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[INFO] Message sent successfully")
            return "sent"  # dummy timestamp
        else:
            print(f"[ERROR] Slack API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to send Slack message: {e}")
        return None


def send_slack_continuation(title, body, delay=1.5):
    """
    Slack 연속 메시지 전송
    
    Args:
        title: 메시지 제목
        body: 메시지 본문
        delay: 전송 간 대기 시간 (초)
    """
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        print("[WARN] SLACK_WEBHOOK not configured")
        return False
    
    text = f"*{title}*\n{body}"
    
    try:
        # Rate limit 방지를 위한 대기
        time.sleep(delay)
        
        response = requests.post(
            webhook,
            json={"text": text},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[INFO] Continuation message sent successfully")
            return True
        else:
            print(f"[ERROR] Slack API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to send continuation message: {e}")
        return False


def send_slack_thread(thread_ts, title, body):
    """
    Backward compatibility wrapper for thread messages
    """
    return send_slack_continuation(title, body)


def send_slack_single_long(title, all_body, max_length=39000):
    """
    하나의 긴 메시지로 전송 (Slack 40KB 제한 고려)
    
    Args:
        title: 메시지 제목
        all_body: 전체 본문
        max_length: 최대 문자 길이
    """
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        print("[WARN] SLACK_WEBHOOK not configured")
        return False
    
    full_text = f"*{title}*\n{all_body}"
    
    # 길이 체크
    if len(full_text) > max_length:
        print(f"[WARN] Message too long ({len(full_text)} chars), truncating...")
        full_text = full_text[:max_length] + "\n\n_... 메시지가 너무 길어 잘렸습니다_"
    
    try:
        response = requests.post(
            webhook,
            json={"text": full_text},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"[INFO] Long message sent successfully ({len(full_text)} chars)")
            return True
        else:
            print(f"[ERROR] Slack API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to send long message: {e}")
        return False