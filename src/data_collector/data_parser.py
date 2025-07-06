"""
데이터 파싱 모듈
스크래핑한 법령 데이터를 파싱하고 청킹하는 모듈
"""

import logging
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LawParser:
    """법령 데이터 파싱 클래스"""
    
    def __init__(self):
        """초기화"""
        # 정규식 패턴 정의
        self.part_pattern = r"제[0-9]{1,2}편"
        self.chapter_pattern = r"제[0-9]{1,2}장"
        self.section_pattern = r"제[0-9]{1,2}절"
        self.article_pattern = r"(제[0-9]+조(?:의[0-9]+)?)\(([^)]+)\)"
        
    def chunk_by_article(self, decree: str, main_rules: List[Tag]) -> List[Dict[str, Any]]:
        """
        법령 데이터를 조문별로 청킹
        
        Args:
            decree: 법령명
            main_rules: BeautifulSoup Tag 리스트
            
        Returns:
            청킹된 법령 데이터 리스트
        """
        chunks = []
        
        # 현재 구조 정보 저장
        part_idx, part_name = None, None
        chapter_idx, chapter_name = None, None
        section_idx, section_name = None, None
        
        logger.info(f"{decree} 파싱 시작 - 총 {len(main_rules)}개 항목")
        
        for idx, main_rule in enumerate(main_rules):
            try:
                # 편/장/절 파싱
                gtit = main_rule.find('p', class_='gtit')
                if gtit:
                    text = gtit.get_text(strip=True)
                    
                    if re.match(self.part_pattern, text):
                        part_idx, part_name = self._parse_title(text)
                        chapter_idx, chapter_name = None, None
                        section_idx, section_name = None, None
                        logger.debug(f"편 파싱: {part_idx} - {part_name}")
                        
                    elif re.match(self.chapter_pattern, text):
                        chapter_idx, chapter_name = self._parse_title(text)
                        section_idx, section_name = None, None
                        logger.debug(f"장 파싱: {chapter_idx} - {chapter_name}")
                        
                    elif re.match(self.section_pattern, text):
                        section_idx, section_name = self._parse_title(text)
                        logger.debug(f"절 파싱: {section_idx} - {section_name}")
                
                # 조문 파싱
                lawcon = main_rule.find('div', class_='lawcon')
                if lawcon:
                    chunk = self._parse_article(
                        lawcon, decree, part_idx, part_name,
                        chapter_idx, chapter_name, section_idx, section_name
                    )
                    if chunk:
                        chunks.append(chunk)
                        
            except Exception as e:
                logger.error(f"파싱 오류 (항목 {idx}): {e}")
                continue
        
        logger.info(f"{decree} 파싱 완료 - 총 {len(chunks)}개 조문")
        return chunks
    
    def _parse_title(self, text: str) -> tuple[str, str]:
        """
        제목 텍스트를 번호와 명칭으로 분리
        
        Args:
            text: 제목 텍스트
            
        Returns:
            (번호, 명칭) 튜플
        """
        parts = text.split(' ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            return parts[0], ""
    
    def _parse_article(self, lawcon: Tag, decree: str, part_idx: Optional[str], 
                      part_name: Optional[str], chapter_idx: Optional[str], 
                      chapter_name: Optional[str], section_idx: Optional[str], 
                      section_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        조문 정보를 파싱하여 딕셔너리로 반환
        
        Args:
            lawcon: 조문 HTML 태그
            decree: 법령명
            part_idx, part_name: 편 정보
            chapter_idx, chapter_name: 장 정보
            section_idx, section_name: 절 정보
            
        Returns:
            파싱된 조문 정보 딕셔너리
        """
        label = lawcon.find('label')
        if not label:
            return None
            
        article_title = label.text.strip()
        match = re.match(self.article_pattern, article_title)
        
        if not match:
            return None
            
        article_idx, article_name = match.groups()
        
        # 조문 내용 추출
        title_length = len(article_title)
        full_text = lawcon.get_text(separator='\n', strip=True)
        
        # 제목 부분을 제외한 본문 추출
        if len(full_text) > title_length:
            article_body = full_text[title_length:].strip()
            # 맨 앞의 개행 문자 제거
            if article_body.startswith('\n'):
                article_body = article_body[1:]
        else:
            article_body = ""
        
        chunk = {
            "법령": decree,
            "편": part_idx,
            "편명": part_name,
            "장": chapter_idx,
            "장명": chapter_name,
            "절": section_idx,
            "절명": section_name,
            "조문번호": article_idx,
            "조문명": article_name,
            "조문내용": article_body
        }
        
        return chunk
    
    def parse_multiple_laws(self, scraped_data: Dict[str, tuple]) -> Dict[str, List[Dict[str, Any]]]:
        """
        여러 법령 데이터를 파싱
        
        Args:
            scraped_data: {법령명: (main_rules, appendix)} 딕셔너리
            
        Returns:
            {법령명: 청킹된_데이터} 딕셔너리
        """
        parsed_data = {}
        
        for law_name, (main_rules, appendix) in scraped_data.items():
            logger.info(f"파싱 시작: {law_name}")
            
            # 본문 파싱
            chunks = self.chunk_by_article(law_name, main_rules)
            
            # 부칙 파싱 (필요한 경우)
            if appendix:
                appendix_chunks = self.chunk_by_article(f"{law_name}_부칙", appendix)
                chunks.extend(appendix_chunks)
            
            parsed_data[law_name] = chunks
            logger.info(f"파싱 완료: {law_name} - 총 {len(chunks)}개 조문")
            
        return parsed_data
    
    def get_statistics(self, parsed_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        파싱된 데이터의 통계 정보 반환
        
        Args:
            parsed_data: 파싱된 데이터
            
        Returns:
            통계 정보 딕셔너리
        """
        stats = {
            "법령수": len(parsed_data),
            "총조문수": sum(len(chunks) for chunks in parsed_data.values()),
            "법령별조문수": {law: len(chunks) for law, chunks in parsed_data.items()},
            "평균조문길이": 0,
            "최장조문길이": 0,
            "최단조문길이": float('inf')
        }
        
        all_chunks = []
        for chunks in parsed_data.values():
            all_chunks.extend(chunks)
        
        if all_chunks:
            content_lengths = [len(chunk["조문내용"]) for chunk in all_chunks]
            stats["평균조문길이"] = sum(content_lengths) / len(content_lengths)
            stats["최장조문길이"] = max(content_lengths)
            stats["최단조문길이"] = min(content_lengths)
        
        return stats


def main():
    """메인 함수 - 테스트용"""
    # 테스트용 더미 데이터 생성
    from bs4 import BeautifulSoup
    
    html_content = """
    <div class="pgroup">
        <p class="gtit">제1편 총칙</p>
    </div>
    <div class="pgroup">
        <div class="lawcon">
            <label>제1조(목적)</label>
            이 법은 범죄의 처벌과 보안처분에 관하여 규정함을 목적으로 한다.
        </div>
    </div>
    """
    
    soup = BeautifulSoup(html_content, 'html.parser')
    main_rules = soup.find_all('div', class_='pgroup')
    
    parser = LawParser()
    chunks = parser.chunk_by_article("테스트법", main_rules)
    
    print(f"파싱 결과: {len(chunks)}개 조문")
    for chunk in chunks:
        print(f"- {chunk['조문번호']}: {chunk['조문명']}")


if __name__ == "__main__":
    main() 