"""
임베딩 모듈  
OpenAI 임베딩과 FAISS 벡터 저장소를 사용하여 문서 임베딩 처리
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDBManager:
    """FAISS 벡터 저장소 관리 클래스
    LangGraph와의 호환을 위해 유사도 검색 메소드는 구현 안함
    """
    
    def __init__(self, embedding_model_id: str = "text-embedding-3-small"):
        """
        초기화
        
        Args:
            embedding_model_id: 사용할 임베딩 모델 ID
            openai_api_key: OpenAI API 키 (None인 경우 .env 파일 또는 환경변수에서 로드)
        """
        self.embedding_model_id = embedding_model_id
        
        # .env 파일 로드 (프로젝트 루트에서 찾기)
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        load_dotenv(env_path)
        
        # OpenAI API 키 설정
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API 키가 필요합니다. .env 파일에 OPENAI_API_KEY를 설정하세요.")
        
        # 임베딩 모델 초기화
        self.embeddings = OpenAIEmbeddings(model=self.embedding_model_id)
        
        # 벡터 저장소 초기화
        self.vector_store = None
        
        logger.info(f"VectorDBManager 초기화 완료 - 모델: {embedding_model_id}")
    
    def create_vector_store(self) -> FAISS:
        """
        새로운 FAISS 벡터 저장소 생성
        
        Returns:
            FAISS 벡터 저장소
        """
        try:
            # 임베딩 차원 크기 계산
            sample_embedding = self.embeddings.embed_query("hello world")
            embedding_dim = len(sample_embedding)
            
            # FAISS 인덱스 생성
            index = faiss.IndexFlatL2(embedding_dim)
            
            # FAISS 벡터 저장소 생성
            vector_store = FAISS(
                embedding_function=self.embeddings,
                docstore=InMemoryDocstore(),
                index=index,
                index_to_docstore_id={},
            )
            
            logger.info(f"벡터 저장소 생성 완료 - 임베딩 차원: {embedding_dim}")
            return vector_store
            
        except Exception as e:
            logger.error(f"벡터 저장소 생성 실패: {e}")
            raise
    
    def add_documents_to_vector_store(self, documents: List[Document], doc_ids: List[str]) -> FAISS:
        """
        문서들을 벡터 저장소에 추가
        
        Args:
            documents: Document 리스트
            doc_ids: 문서 ID 리스트
            
        Returns:
            문서가 추가된 FAISS 벡터 저장소
        """
        if not documents:
            raise ValueError("추가할 문서가 없습니다.")
        
        if len(documents) != len(doc_ids):
            raise ValueError("문서 수와 ID 수가 일치하지 않습니다.")
        
        try:
            # 새로운 벡터 저장소 생성
            if self.vector_store is None:
                self.vector_store = self.create_vector_store()
            
            # 문서들을 배치로 추가
            batch_size = 100
            total_docs = len(documents)
            
            logger.info(f"문서 임베딩 시작 - 총 {total_docs}개 문서")
            
            for i in range(0, total_docs, batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_ids = doc_ids[i:i + batch_size]
                
                # 배치 추가
                self.vector_store.add_documents(documents=batch_docs, ids=batch_ids)
                
                processed = min(i + batch_size, total_docs)
                logger.info(f"진행률: {processed}/{total_docs} ({processed/total_docs*100:.1f}%)")
            
            logger.info(f"문서 임베딩 완료 - 총 {total_docs}개 문서 추가")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"문서 임베딩 실패: {e}")
            raise
    
    def save_vector_store(self, save_path: Path) -> None:
        """
        벡터 저장소를 디스크에 저장
        
        Args:
            save_path: 저장할 디렉터리 경로
        """
        if self.vector_store is None:
            raise ValueError("저장할 벡터 저장소가 없습니다.")
        
        try:
            # 디렉터리 생성
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 벡터 저장소 저장
            self.vector_store.save_local(str(save_path))
            
            logger.info(f"벡터 저장소 저장 완료: {save_path}")
            
        except Exception as e:
            logger.error(f"벡터 저장소 저장 실패: {e}")
            raise
    
    def load_vector_store(self, load_path: Path) -> FAISS:
        """
        디스크에서 벡터 저장소 로드
        
        Args:
            load_path: 로드할 디렉터리 경로
            
        Returns:
            로드된 FAISS 벡터 저장소
        """
        try:
            # 벡터 저장소 로드
            self.vector_store = FAISS.load_local(
                str(load_path), 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            logger.info(f"벡터 저장소 로드 완료: {load_path}")
            return self.vector_store
            
        except Exception as e:
            logger.error(f"벡터 저장소 로드 실패: {e}")
            raise
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """
        벡터 저장소 통계 정보 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        if self.vector_store is None:
            return {"문서수": 0, "인덱스크기": 0}
        
        try:
            # 인덱스 크기 가져오기
            index_size = self.vector_store.index.ntotal
            
            # 문서스토어 크기 가져오기
            docstore_size = len(self.vector_store.docstore._dict)
            
            stats = {
                "문서수": docstore_size,
                "인덱스크기": index_size,
                "임베딩모델": self.embedding_model_id,
                "벡터저장소타입": "FAISS"
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 정보 가져오기 실패: {e}")
            return {"문서수": 0, "인덱스크기": 0}


def main():
    """테스트용 메인 함수"""
    # 테스트 문서 생성
    test_docs = [
        Document(
            page_content="형법 제1조 범죄의 정의",
            metadata={"법령": "형법", "조문번호": "제1조", "조문명": "범죄의 정의"}
        ),
        Document(
            page_content="형법 제2조 형의 종류",
            metadata={"법령": "형법", "조문번호": "제2조", "조문명": "형의 종류"}
        )
    ]
    test_ids = ["형법 제1조", "형법 제2조"]
    
    # VectorDBManager 초기화
    manager = VectorDBManager()
    
    # 문서 임베딩
    vector_store = manager.add_documents_to_vector_store(test_docs, test_ids)
    
    # 통계 출력
    stats = manager.get_vector_store_stats()
    print("=" * 50)
    print("벡터 저장소 통계")
    print("=" * 50)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 유사도 검색 테스트
    results = vector_store.similarity_search("형법", k=2)
    print("\n" + "=" * 50)
    print("유사도 검색 결과")
    print("=" * 50)
    for i, doc in enumerate(results, 1):
        print(f"{i}. {doc.page_content[:50]}...")


if __name__ == "__main__":
    main() 