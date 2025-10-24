import os
import time
import google.generativeai as genai
from typing import List, Dict, Optional

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
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
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
        summary = item.get('summary', '').strip()
        
        try:
            if summary:
                # 초록이 있는 경우: 요약
                prompt = f"""다음 AI 뉴스의 초록을 한국어로 간단히 요약해주세요 (2-3문장):

제목: {title}
초록: {summary}

요약:"""
            else:
                # 초록이 없는 경우: 제목만 번역
                prompt = f"""다음 AI 뉴스 제목을 자연스러운 한국어로 번역해주세요:

{title}

번역:"""
            
            response = self.model.generate_content(prompt)
            summary_ko = response.text.strip()
            
            # 결과 저장
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
    summarizer = GeminiSummarizer()
    
    # 테스트 데이터
    test_items = [
        {
            'title': 'OpenAI Announces GPT-5 with Advanced Reasoning',
            'summary': 'OpenAI today unveiled GPT-5, featuring enhanced reasoning capabilities and multimodal understanding. The new model shows significant improvements in complex problem-solving tasks.',
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


if __name__ == "__main__":
    test_summarizer()