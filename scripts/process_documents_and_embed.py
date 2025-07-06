#!/usr/bin/env python3
"""
문서 처리 및 임베딩 스크립트
data/raw의 JSON 파일들을 Document로 변환하고 FAISS 벡터 저장소에 임베딩
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# 프로젝트 루트 디렉터리를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
env_path = project_root / ".env"
load_dotenv(env_path)

from src.vector_db.document_processor import DocumentProcessor
from src.vector_db.embeddings import VectorDBManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("법령 문서 처리 및 임베딩 시작")
    logger.info("=" * 60)
    
    # 디렉터리 경로 설정
    data_raw_dir = project_root / "data" / "raw"
    data_embeddings_dir = project_root / "data" / "embeddings"
    
    # 디렉터리 존재 확인
    if not data_raw_dir.exists():
        logger.error(f"원시 데이터 디렉터리가 존재하지 않습니다: {data_raw_dir}")
        return
    
    # 임베딩 디렉터리 생성
    data_embeddings_dir.mkdir(parents=True, exist_ok=True)
    
    # OpenAI API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정하세요.")
        return
    
    try:
        # 1. Document 처리 모듈 초기화
        logger.info("1. Document 처리 모듈 초기화")
        doc_processor = DocumentProcessor()
        
        # 2. 벡터DB 관리자 초기화
        logger.info("2. 벡터DB 관리자 초기화")
        vector_manager = VectorDBManager(embedding_model_id="text-embedding-3-small")
        
        # 3. 원시 데이터 처리
        logger.info("3. 원시 데이터 처리 시작")
        logger.info(f"원시 데이터 디렉터리: {data_raw_dir}")
        
        # 모든 JSON 파일 처리하여 Document 생성
        documents, doc_ids = doc_processor.process_law_directory(data_raw_dir)
        
        if not documents:
            logger.error("처리할 문서가 없습니다.")
            return
        
        # Document 통계 출력
        doc_stats = doc_processor.get_statistics(documents)
        logger.info("문서 처리 통계:")
        for key, value in doc_stats.items():
            logger.info(f"  {key}: {value}")
        
        # 4. 문서 임베딩 처리
        logger.info("4. 문서 임베딩 처리 시작")
        logger.info(f"임베딩할 문서 수: {len(documents)}")
        
        # 벡터 저장소에 문서 추가
        vector_store = vector_manager.add_documents_to_vector_store(documents, doc_ids)
        
        # 5. 벡터 저장소 저장
        logger.info("5. 벡터 저장소 저장")
        vector_manager.save_vector_store(data_embeddings_dir)
        
        # 6. 최종 통계 출력
        logger.info("6. 최종 결과 통계")
        vector_stats = vector_manager.get_vector_store_stats()
        
        logger.info("=" * 60)
        logger.info("처리 완료 결과")
        logger.info("=" * 60)
        logger.info(f"처리된 문서 수: {len(documents)}")
        logger.info(f"생성된 ID 수: {len(doc_ids)}")
        logger.info(f"벡터 저장소 통계:")
        for key, value in vector_stats.items():
            logger.info(f"  {key}: {value}")
        logger.info(f"저장 위치: {data_embeddings_dir}")
        
        # 7. 간단한 검색 테스트 (FAISS 객체 직접 사용)
        logger.info("7. 검색 기능 테스트")
        test_queries = ["형법", "도로교통법", "마약"]
        
        for query in test_queries:
            try:
                # VectorDBManager가 아닌 FAISS 객체에서 직접 검색
                results = vector_store.similarity_search(query, k=3)
                logger.info(f"검색어 '{query}' 결과 {len(results)}개:")
                for i, doc in enumerate(results, 1):
                    law_name = doc.metadata.get("법령", "Unknown")
                    article_num = doc.metadata.get("조문번호", "Unknown")
                    logger.info(f"  {i}. {law_name} {article_num}")
            except Exception as e:
                logger.error(f"검색 테스트 실패 - '{query}': {e}")
        
        logger.info("=" * 60)
        logger.info("법령 문서 처리 및 임베딩 완료")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main() 