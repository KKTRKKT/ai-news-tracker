# 🤖 AI News Tracker with Gemini Summary

RSS 피드에서 AI 뉴스를 자동 수집하고, Google Gemini API로 한국어 요약/번역하여 Slack으로 전송하는 GitHub Actions 기반 자동화 시스템입니다.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)

## ✨ 주요 기능

- 📡 **12개 RSS 피드 자동 수집**: OpenAI, Hugging Face, Google AI, MIT Tech Review 등
- 🤖 **AI 기반 요약**: Gemini API로 영문 초록을 한국어로 요약 (2-3문장)
- 🌐 **스마트 번역**: 초록이 없는 경우 제목만 자연스럽게 한국어로 번역
- 🔔 **Slack 실시간 알림**: 
  - 매일 오전 9시 전날 뉴스 요약 발송
  - 매시간 신규 뉴스 자동 감지 및 알림
- 🎯 **중복 제거**: 이미 본 뉴스는 자동 필터링
- 📊 **유연한 전송 모드**: 단일/다중 메시지 선택 가능

## 📸 스크린샷

### Daily Summary (MULTIPLE 모드)
```
📌 2025-10-26 AI 뉴스 요약 (86건) 🤖

🔤 [VentureBeat AI] 인간 클릭에서 머신 의도로: 에이전틱 AI를 위한 웹 준비
  (10/26 13:00)
  https://venturebeat.com/ai/...

📝 [OpenAI News] OpenAI가 Sky 제작사를 인수하여 AI 통합 강화
  ChatGPT에 새로운 음성 및 화상 통화 기능이 추가될 예정입니다.
  (10/23 19:00)
  https://openai.com/index/...

... 외 76개 항목 (다음 메시지에서 확인)
```

```
📄 계속 (1/4) - 11~30번

🔤 [Hugging Face Blog] ...
...
```

## 🚀 빠른 시작 (5분 설정)

### 1단계: 저장소 포크

1. 이 저장소 우측 상단의 **Fork** 버튼 클릭
2. 자신의 GitHub 계정으로 포크

### 2단계: Gemini API 키 발급

1. [Google AI Studio](https://aistudio.google.com/apikey) 접속
2. **"Get API Key"** → **"Create API key in new project"** 클릭
3. 생성된 API 키 복사 (예: `AIzaSyD...`)

> 💡 **무료 티어**: 분당 15회, 일일 1,500회 요청 가능

### 3단계: Slack Webhook 설정

1. Slack 워크스페이스에서 [Incoming Webhooks](https://api.slack.com/messaging/webhooks) 앱 추가
2. 알림을 받을 채널 선택 (예: `#ai-news`)
3. Webhook URL 복사 (예: `https://hooks.slack.com/services/T00000000/...`)

### 4단계: GitHub Secrets 설정

포크한 저장소에서:

1. **Settings** → **Secrets and variables** → **Actions** 클릭
2. **New repository secret** 클릭하여 다음 2개 추가:

| Name | Value | 설명 |
|------|-------|------|
| `GEMINI_API_KEY` | `AIzaSyD...` | 2단계에서 복사한 Gemini API 키 |
| `SLACK_WEBHOOK` | `https://hooks.slack.com/services/...` | 3단계에서 복사한 Webhook URL |

### 5단계: GitHub Actions 활성화

1. 포크한 저장소에서 **Actions** 탭 클릭
2. **"I understand my workflows, go ahead and enable them"** 클릭
3. 좌측 메뉴에서 **"Daily Summary (KST 09:00)"** 선택
4. **"Run workflow"** 버튼으로 즉시 테스트 가능! 🎉

## ⚙️ 상세 설정

### 환경변수 커스터마이징

`.github/workflows/daily-summary.yml` 또는 `hourly-check.yml` 파일을 수정하세요:

```yaml
- name: Run daily summary
  env:
    MODE: DAILY_SUMMARY           # 모드: DAILY_SUMMARY | HOURLY_CHECK
    TIMEZONE: Asia/Seoul          # 타임존 (기본: Asia/Seoul)
    USE_GEMINI: "true"            # Gemini API 사용 (true/false)
    SEND_MODE: "MULTIPLE"         # 전송 모드 (MULTIPLE/SINGLE)
    ITEMS_PER_MESSAGE: "10"       # 첫 메시지 항목 수 (기본: 10)
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: python main.py
```

### 전송 모드 비교

| 모드 | 설명 | 장점 | 단점 | 권장 상황 |
|------|------|------|------|----------|
| **MULTIPLE** | 첫 N개 + 연속 메시지 | 깔끔한 알림, 스크롤 부담 감소 | 여러 메시지 생성 | **일일 요약 (권장)** |
| **SINGLE** | 모든 항목을 하나의 메시지로 | 전체 내용 한눈에 확인 | 긴 메시지, 40KB 제한 | 신규 항목이 적을 때 |

### 스케줄 변경

```yaml
on:
  schedule:
    - cron: "0 0 * * *"   # 09:00 KST (00:00 UTC)
    # 다른 시간으로 변경하려면:
    # - cron: "0 12 * * *"  # 21:00 KST (12:00 UTC)
```

> 💡 **시간 계산**: UTC 기준이므로 KST에서 -9시간

### RSS 피드 추가/수정

`feeds.yaml` 파일을 수정하여 원하는 피드를 추가할 수 있습니다:

```yaml
feeds:
  - name: 내가 추가한 블로그
    url: https://example.com/feed.xml
  
  - name: OpenAI News
    url: https://openai.com/news/rss.xml
  # ... 기존 피드들
```

## 🔧 로컬 테스트

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/ai-news-tracker.git
cd ai-news-tracker

# 2. 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
export GEMINI_API_KEY="your-api-key"
export SLACK_WEBHOOK="your-webhook-url"
export MODE="HOURLY_CHECK"
export USE_GEMINI="true"
export SEND_MODE="MULTIPLE"

# 5. 실행
python main.py
```

### Gemini API 단독 테스트

```bash
export GEMINI_API_KEY="your-api-key"
python gemini_summarizer.py
```

### 사용 가능한 Gemini 모델 확인

```bash
export GEMINI_API_KEY="your-api-key"
python check_models.py
```

## 📊 파일 구조

```
ai-news-tracker/
├── 📄 README.md                    # 이 파일
├── 📄 requirements.txt             # Python 의존성
├── 📄 feeds.yaml                   # RSS 피드 목록 설정
│
├── 🐍 main.py                      # 메인 실행 파일
├── 🐍 gemini_summarizer.py         # Gemini API 래퍼 (REST API)
├── 🐍 notifier.py                  # Slack 알림 모듈
├── 🐍 utils.py                     # 유틸리티 함수 (날짜, 정규화)
├── 🐍 state.py                     # 중복 제거 상태 관리
├── 🐍 check_models.py              # Gemini 모델 확인 도구
│
├── 📁 .github/workflows/
│   ├── daily-summary.yml           # 일일 요약 (매일 09:00 KST)
│   └── hourly-check.yml            # 시간별 신규 체크 (매시간)
│
└── 📁 data/                        # 자동 생성됨
    └── seen-2025-10-26.json        # 일별 중복 제거 데이터
```

## 💰 비용 및 제한사항

### Gemini API (무료 티어)

| 항목 | 제한 |
|------|------|
| 요청 수 | 분당 15회, 일일 1,500회 |
| 처리 속도 | 항목당 약 1.2초 (rate limit 방지) |
| 예상 시간 | 10개: ~12초, 100개: ~2분 |

### 권장 사용량

- **Daily Summary**: 하루 1회 (100개 항목 = 100 요청)
- **Hourly Check**: 24회/일 (평균 0-5개 = 0-120 요청)
- **총 예상**: ~220 요청/일 (무료 티어 1,500회의 15%)

### GitHub Actions

- 무료 티어: 월 2,000분 (public 저장소는 무제한)
- 이 프로젝트 사용량: 약 5분/일

## 🎨 아이콘 가이드

| 아이콘 | 의미 |
|--------|------|
| 📝 | 초록이 있어서 **요약**된 항목 |
| 🔤 | 제목만 **번역**된 항목 |
| 🤖 | Gemini API 처리 완료 |
| 📌 | Daily Summary 메시지 |
| 🆕 | 신규 항목 감지 |
| 📄 | 연속 메시지 (N/M) |

## 🐛 트러블슈팅

### 문제 1: Gemini API 404 오류

```
Error: 404 models/gemini-1.5-flash is not found
```

**해결방법:**

```bash
# 1. 사용 가능한 모델 확인
python check_models.py

# 2. gemini_summarizer.py 22번째 줄 수정
self.model = "gemini-pro"  # 또는 check_models.py에서 확인한 모델
```

### 문제 2: API 키 오류

```
Error: GEMINI_API_KEY가 설정되지 않았습니다
```

**해결방법:**
- GitHub Secrets에 `GEMINI_API_KEY`가 정확히 추가되었는지 확인
- 키에 공백이나 잘못된 문자가 없는지 확인
- API 키가 활성화되어 있는지 Google AI Studio에서 확인

### 문제 3: Rate Limit 초과

```
Error: 429 Resource exhausted
```

**해결방법:**
- **임시 해결**: 워크플로우에서 `USE_GEMINI: "false"` 설정
- **영구 해결**: Google Cloud에서 유료 API 키 발급
- 24시간 후 자동으로 제한 리셋

### 문제 4: Slack 알림이 안 와요

**체크리스트:**
- [ ] Slack Webhook URL이 `https://hooks.slack.com/services/`로 시작하는지 확인
- [ ] GitHub Secrets에 `SLACK_WEBHOOK` 정확히 추가
- [ ] Slack 채널에서 Incoming Webhooks 앱이 활성화되어 있는지 확인
- [ ] GitHub Actions의 로그에서 `[INFO] Message sent successfully` 확인

### 문제 5: 메시지가 너무 길어요

```
[WARN] Message too long (45000 chars), truncating...
```

**해결방법:**

```yaml
# 워크플로우에서 설정 변경
SEND_MODE: "MULTIPLE"      # SINGLE → MULTIPLE로 변경
ITEMS_PER_MESSAGE: "5"     # 10 → 5로 줄이기
```

### 문제 6: 중복 뉴스가 계속 와요

**해결방법:**
- `data/seen-YYYY-MM-DD.json` 파일이 정상적으로 커밋되는지 확인
- 워크플로우 로그에서 `[INFO] Saved N items to seen set` 확인
- 문제가 계속되면 `data/` 폴더의 모든 파일 삭제 후 재실행

## 📈 고급 활용

### 여러 Slack 채널에 전송

각 채널마다 별도의 Webhook을 만들고:

```yaml
# .github/workflows/daily-summary-team1.yml
env:
  SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_TEAM1 }}

# .github/workflows/daily-summary-team2.yml
env:
  SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK_TEAM2 }}
```

### 특정 키워드만 필터링

`main.py`에 필터링 로직 추가:

```python
def filter_by_keywords(items, keywords):
    """특정 키워드가 포함된 항목만 필터링"""
    return [
        item for item in items 
        if any(kw.lower() in item['title'].lower() for kw in keywords)
    ]

# main() 함수에서:
keywords = ["GPT", "Claude", "LLM", "transformer"]
filtered_items = filter_by_keywords(sorted_items, keywords)
```

### Discord로 전송

`notifier.py`에 Discord webhook 함수 추가:

```python
def send_discord(title, body):
    webhook = os.getenv("DISCORD_WEBHOOK")
    if not webhook:
        return
    
    payload = {
        "content": f"**{title}**\n{body}"
    }
    requests.post(webhook, json=payload, timeout=10)
```

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스를 사용합니다:

- [feedparser](https://github.com/kurtmckee/feedparser) - RSS 파싱
- [Google Gemini API](https://ai.google.dev/) - AI 요약/번역
- [Slack API](https://api.slack.com/) - 메시지 전송
- [GitHub Actions](https://github.com/features/actions) - 자동화
