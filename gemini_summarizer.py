import os, re, time
import google.generativeai as genai
from typing import List, Dict, Optional

# RSS 초록의 최대 길이 (Gemini 프롬프트 크기 절약)
MAX_SUMMARY_LENGTH = 1500

class GeminiSummarizer:
    def __init__(self, api_key: Optional[str] = None):
        """
        Gemini API를 사용한 뉴스 요약/번역기

        Args:
            api_key: Gemini API 키 (없으면 환경변수 GEMINI_API_KEY 사용)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다")

        genai.configure(api_key=self.api_key)

        # 사용 가능한 모델 리스트 확인 및 선택
        try:
            model_candidates = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash',
                'gemini-pro',
                'gemini-1.0-pro'
            ]

            available_models = [m.name for m in genai.list_models()]
            print(f"[DEBUG] Available models: {available_models[:5]}...")

            selected_model = None
            for candidate in model_candidates:
                if f'models/{candidate}' in available_models or candidate in available_models:
                    selected_model = candidate
                    break

            if not selected_model:
                for model_info in genai.list_models():
                    if 'generateContent' in model_info.supported_generation_methods:
                        selected_model = model_info.name.replace('models/', '')
                        break

            if not selected_model:
                raise ValueError("사용 가능한 Gemini 모델을 찾을 수 없습니다")

            print(f"[INFO] Using Gemini model: {selected_model}")
            self.model = genai.GenerativeModel(selected_model)

        except Exception as e:
            print(f"[ERROR] 모델 초기화 오류: {e}")
            raise

    @staticmethod
    def _clean_html(text: str) -> str:
        """
        RSS 초록에서 HTML 태그를 제거한다.
        많은 피드(특히 VentureBeat, MIT Tech Review 등)가
        <p>, <a>, <img>, <span> 등의 HTML을 초록에 포함시킨다.
        """
        if not text:
            return ""

        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', ' ', text)

        # HTML 엔티티 복원
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&apos;': "'",
            '&nbsp;': ' ',
            '&#8217;': '\u2019',  # 오른쪽 작은따옴표
            '&#8216;': '\u2018',  # 왼쪽 작은따옴표
            '&#8220;': '\u201c',  # 왼쪽 큰따옴표
            '&#8221;': '\u201d',  # 오른쪽 큰따옴표
            '&#8230;': '…',      # 줄임표
        }
        for entity, char in html_entities.items():
            text = text.replace(entity, char)

        # 중복 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def summarize_item(self, item: Dict) -> Dict:
        """
        단일 뉴스 아이템 처리
        - 초록이 있으면 한국어로 요약
        - 초록이 없으면 제목만 한국어로 번역

        Args:
            item: 뉴스 아이템 딕셔너리 (title, link, summary 등 포함)

        Returns:
            원본 아이템 + 'summary_ko' 필드 추가된 딕셔너리
        """
        title = item.get('title', '')
        # HTML 정리 후 길이 제한
        summary = self._clean_html(item.get('summary', ''))
        if len(summary) > MAX_SUMMARY_LENGTH:
            summary = summary[:MAX_SUMMARY_LENGTH] + "..."
            print(f"[INFO] Summary truncated for: {title[:40]}...")

        try:
            if summary:
                prompt = f"""다음 AI 뉴스의 초록을 한국어로 간단히 요약해주세요 (2-3문장):

제목: {title}
초록: {summary}

요약:"""
            else:
                prompt = f"""다음 AI 뉴스 제목을 자연스러운 한국어로 번역해주세요:

{title}

번역:"""

            response = self.model.generate_content(prompt)
            summary_ko = response.text.strip()

            item['summary_ko'] = summary_ko
            item['has_summary'] = bool(summary)

            print(f"[INFO] Processed: {title[:50]}...")

        except Exception as e:
            print(f"[ERROR] Gemini API 오류: {e}")
            # 실패시 원본 제목 사용
            item['summary_ko'] = title
            item['has_summary'] = False

        return item

    def batch_summarize(self, items: List[Dict], delay: float = 1.0) -> List[Dict]:
        """
        여러 뉴스 아이템 일괄 처리

        Args:
            items: 뉴스 아이템 리스트
            delay: API 호출 간 대기 시간 (초)

        Returns:
            처리된 아이템 리스트
        """
        processed_items = []

        for i, item in enumerate(items, 1):
            print(f"[INFO] Processing {i}/{len(items)}...")
            processed = self.summarize_item(item)
            processed_items.append(processed)

            # API rate limit 방지
            if i < len(items):
                time.sleep(delay)

        return processed_items


def test_summarizer():
    """테스트 함수"""
    try:
        # HTML 정리 테스트
        test_html = '<p>OpenAI today unveiled <strong>GPT-5</strong>, featuring <a href="https://example.com">enhanced reasoning</a> capabilities.</p><p>The new model shows &amp; significant improvements.</p>'
        cleaned = GeminiSummarizer._clean_html(test_html)
        print(f"HTML 정리 테스트:")
        print(f"  입력: {test_html}")
        print(f"  출력: {cleaned}")
        print()

        summarizer = GeminiSummarizer()

        test_items = [
            {
                'title': 'OpenAI Announces GPT-5 with Advanced Reasoning',
                'summary': '<p>OpenAI today unveiled <strong>GPT-5</strong>, featuring enhanced reasoning capabilities and multimodal understanding.</p><p>The new model shows significant improvements in complex problem-solving tasks.</p>',
                'link': 'https://example.com/gpt5'
            },
            {
                'title': 'Google DeepMind Releases New AlphaFold Version',
                'summary': '',  # 초록 없음
                'link': 'https://example.com/alphafold'
            }
        ]

        results = summarizer.batch_summarize(test_items)

        print("\n=== 결과 ===")
        for item in results:
            print(f"\n제목: {item['title']}")
            print(f"요약/번역: {item['summary_ko']}")
            print(f"초록 존재: {item['has_summary']}")
    except Exception as e:
        print(f"[ERROR] 테스트 실패: {e}")


if __name__ == "__main__":
    test_summarizer()