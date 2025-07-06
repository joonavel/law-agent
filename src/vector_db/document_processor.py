"""
문서 처리 모듈
JSON 형태의 법령 데이터를 LangChain Document로 변환하는 모듈
"""

import json
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from langchain_core.documents import Document

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """법령 데이터를 Document로 변환하는 클래스"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def create_content(self, chunk: Dict[str, Any]) -> str:
        """
        청크 데이터에서 document의 page_content 생성
        
        Args:
            chunk: 법령 조문 단위의 청크 데이터
            
        Returns:
            생성된 콘텐츠 문자열
        """
        content = ""
        content += f"{chunk['법령']} {chunk['조문번호']}\n"
        
        # 편명 추가 (있는 경우) - 편명은 의미가 없어 생략
        # if chunk['편명']:
        #     content += f"{chunk['편명']}\n"
        
        # 장명 추가 (있는 경우)
        if chunk['장명']:
            content += f"{chunk['장명']}\n"
            
        # 절명 추가 (있는 경우)
        if chunk['절명']:
            content += f"{chunk['절명']}\n"
            
        # 조문명과 조문내용 추가
        content += chunk['조문명'] + "\n" + chunk['조문내용']
        
        return content
    
    def get_docs_and_ids(self, chunks: List[Dict[str, Any]]) -> Tuple[List[Document], List[str]]:
        """
        청크 리스트에서 Document와 ID 생성
        ID는 법령의 이름과 조문번호로 구성 [법령 조문번호] 형식 ex) 형법 제1조, 형사소송법 제10조의2
        
        Args:
            chunks: 법령 청크 데이터 리스트
            
        Returns:
            (Document 리스트, ID 리스트) 튜플
        """
        docs = [
            Document(
                page_content=self.create_content(chunk),
                metadata={
                    "법령": chunk['법령'],
                    "편": chunk['편'],
                    "편명": chunk['편명'],
                    "장": chunk['장'],
                    "장명": chunk['장명'],
                    "절": chunk['절'],
                    "절명": chunk['절명'],
                    "조문번호": chunk['조문번호'],
                    "조문명": chunk['조문명'],
                }
            )
            for chunk in chunks
        ]
        
        doc_ids = [f"{chunk['법령']} {chunk['조문번호']}" for chunk in chunks]
        
        return docs, doc_ids
    
    def load_chunks_from_json(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        JSON 파일에서 청크 데이터 로드
        
        Args:
            file_path: JSON 파일 경로
            
        Returns:
            청크 데이터 리스트
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            logger.info(f"로드 완료: {file_path.name} ({len(chunks)}개 조문)")
            return chunks
            
        except Exception as e:
            logger.error(f"로드 실패: {file_path} - {e}")
            return []
    
    def process_law_directory(self, raw_data_dir: Path) -> Tuple[List[Document], List[str]]:
        """
        전체 법령 디렉터리 처리
        
        Args:
            raw_data_dir: 원시 데이터 디렉터리 경로
            
        Returns:
            (전체 Document 리스트, 전체 ID 리스트) 튜플
        """
        all_docs = []
        all_doc_ids = []
        
        # JSON 파일들 찾기
        json_files = list(raw_data_dir.glob("*.json"))
        logger.info(f"처리할 JSON 파일 수: {len(json_files)}")
        
        for json_file in json_files:
            try:
                # 청크 로드
                chunks = self.load_chunks_from_json(json_file)
                
                if not chunks:
                    logger.warning(f"빈 파일 건너뜀: {json_file.name}")
                    continue
                
                # Document 변환
                docs, doc_ids = self.get_docs_and_ids(chunks)
                
                # 전체 리스트에 추가
                all_docs.extend(docs)
                all_doc_ids.extend(doc_ids)
                
                logger.info(f"처리 완료: {json_file.name} ({len(docs)}개 Document)")
                
            except Exception as e:
                logger.error(f"처리 실패: {json_file.name} - {e}")
                continue
        
        logger.info(f"전체 처리 완료: {len(all_docs)}개 Document, {len(all_doc_ids)}개 ID")
        return all_docs, all_doc_ids
    
    def get_statistics(self, docs: List[Document]) -> Dict[str, Any]:
        """
        Document 통계 정보 반환
        
        Args:
            docs: Document 리스트
            
        Returns:
            통계 정보 딕셔너리
        """
        if not docs:
            return {"총_문서수": 0, "법령별_문서수": {}}
        
        # 법령별 문서 수 계산
        law_counts = {}
        for doc in docs:
            law_name = doc.metadata.get("법령", "Unknown")
            law_counts[law_name] = law_counts.get(law_name, 0) + 1
        
        # 평균 문서 길이 계산
        total_length = sum(len(doc.page_content) for doc in docs)
        avg_length = total_length / len(docs) if docs else 0
        
        stats = {
            "총_문서수": len(docs),
            "법령별_문서수": law_counts,
            "평균_문서길이": round(avg_length, 2),
            "총_문서길이": total_length
        }
        
        return stats


def main():
    """테스트용 메인 함수"""
    processor = DocumentProcessor()
    
    # 테스트 데이터 경로
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    
    # 전체 처리
    docs, doc_ids = processor.process_law_directory(raw_data_dir)
    
    # 통계 출력
    stats = processor.get_statistics(docs)
    print("=" * 50)
    print("Document 처리 통계")
    print("=" * 50)
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main() 