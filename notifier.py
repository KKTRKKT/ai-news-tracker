import os, requests

# Slack 메시지 최대 크기 (바이트) - 안전 여유분 포함
SLACK_MAX_BYTES = 39_000  # 실제 제한은 40KB, 여유분 둄음

def send_slack(title, body):
    """
    Slack Webhook으로 메시지 전송.
    메시지가 제한 크기를 초과하면 자동 절단한다.
    """
    webhook = os.getenv("SLACK_WEBHOOK")
    if not webhook:
        print("[WARN] SLACK_WEBHOOK 환경변수 미설정")
        return

    text = f"*{title}*\n{body}"

    # UTF-8 바이트 길이로 제한 확인 (Slack은 바이트 기준 제한)
    text_bytes = text.encode("utf-8")
    if len(text_bytes) > SLACK_MAX_BYTES:
        print(f"[WARN] Message too long ({len(text_bytes)} bytes), truncating to {SLACK_MAX_BYTES} bytes...")
        # 바이트 경계에서 잘라내면 한글 글자가 깨질 수 있으므로 문자 단위로 절단
        truncated = text
        while len(truncated.encode("utf-8")) > SLACK_MAX_BYTES - 100:  # "...[절단]" 표시용 여유분
            truncated = truncated[:-50]  # 50자씩 줄임
        text = truncated + "\n\n⚠️ ...[메시지 길이 제한으로 절단됨]"
        print(f"[INFO] Truncated to {len(text.encode('utf-8'))} bytes")

    try:
        resp = requests.post(webhook, json={"text": text}, timeout=10)
        resp.raise_for_status()
        print("[INFO] Message sent successfully")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] Slack webhook HTTP 오류: {e.response.status_code} - {e.response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Slack webhook 전송 실패: {e}")