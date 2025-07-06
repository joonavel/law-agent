"""
RAG 검색 도구 모듈
벡터 저장소를 이용한 법령 검색 도구들
"""

import logging
from typing import List, Tuple, Optional, Annotated
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.tools import tool
from dotenv import load_dotenv

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.vector_db.embeddings import VectorDBManager

# .env 파일 로드
env_path = project_root / ".env"
load_dotenv(env_path)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LawRetriever:
    """법령 검색 클래스"""
    
    def __init__(self):
        """초기화 - 벡터 저장소 로드"""
        self.vector_manager = VectorDBManager()
        self.embeddings_path = project_root / "data" / "embeddings"
        
        # 벡터 저장소 로드
        try:
            self.vector_store = self.vector_manager.load_vector_store(self.embeddings_path)
            logger.info("벡터 저장소 로드 완료")
        except Exception as e:
            logger.error(f"벡터 저장소 로드 실패: {e}")
            raise


# 글로벌 retriever 인스턴스 생성
retriever = LawRetriever()


@tool(response_format="content_and_artifact")
def search_article_by_id(
    article_id: Annotated[str, "The article id to search for. It should be in the format of '법령 조문번호' like '형사소송법 제109조의2', '형법 제12조'"]
) -> Tuple[str, Optional[Document]]:
    """Input to this tool should be a string in the format of '법령 조문번호' like '형사소송법 제109조의2', '형법 제12조'. Output is a string of the article content and the document object.
    If the article is not found, return 'No document found' and None. If 'No document found' is returned, fix the article_id and try again.
    '법령' has to be one of the following: 형법, 형사소송법, 폭력행위등처벌에관한법률, 부정수표단속법, 도로교통법, 특정범죄가중처벌등에관한법률, 마약류불법거래방지에관한특례법, 소송촉진등에관한특례법, 벌금미납자의사회봉사집행에관한특례법"""
    
    try:
        temp = retriever.vector_store.get_by_ids([article_id])
        if temp:
            retrieved_doc = temp[0]
            serialized = f"Source: {retrieved_doc.metadata}\n Content: {retrieved_doc.page_content}"
            
            logger.info(f"조문 검색 성공: {article_id}")
            return serialized, retrieved_doc
        else:
            logger.warning(f"조문 검색 실패: {article_id}")
            return "No document found", None
            
    except Exception as e:
        logger.error(f"조문 검색 오류: {e}")
        return "No document found", None


@tool(response_format="content_and_artifact")
def retrieve(
    query: Annotated[str, "The query to retrieve information from the vector store"],
    filter: Annotated[Optional[str], "Name of the decree to apply filter. Here are the supported legal codes: 형법, 형사소송법, 폭력행위등처벌에관한법률, 부정수표단속법, 도로교통법, 특정범죄가중처벌등에관한법률, 마약류불법거래방지에관한특례법, 소송촉진등에관한특례법, 벌금미납자의사회봉사집행에관한특례법"] = None,
    k: Annotated[int, "The number of documents to retrieve"] = 2
) -> Tuple[str, List[Document]]:
    """Inputs to this tool are the query to retrieve, filter to apply to the query, and the number of documents to retrieve.
    Output is a string of the retrieved documents and the document objects.
    If you get empty result, it means that the filter is not supported. Try with no filter.
    filter has to be one of the following: 형법, 형사소송법, 폭력행위등처벌에관한법률, 부정수표단속법, 도로교통법, 특정범죄가중처벌등에관한법률, 마약류불법거래방지에관한특례법, 소송촉진등에관한특례법, 벌금미납자의사회봉사집행에관한특례법"""
    
    try:
        if filter:
            retrieved_docs = retriever.vector_store.similarity_search(
                query, k=k, filter={"법령": filter}
            )
        else:
            retrieved_docs = retriever.vector_store.similarity_search(query, k=k)
            
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )
        
        logger.info(f"벡터 검색 완료: '{query}' (필터: {filter}, 결과: {len(retrieved_docs)}개)")
        return serialized, retrieved_docs
        
    except Exception as e:
        logger.error(f"벡터 검색 오류: {e}")
        return "검색 중 오류가 발생했습니다.", []


def get_rag_tools():
    """RAG 도구 리스트 반환"""
    return [search_article_by_id, retrieve]


def main():
    """테스트용 메인 함수"""
    print("=== RAG 도구 테스트 ===")
    
    # 1. 조문 ID로 검색 테스트
    print("\n1. 조문 ID 검색 테스트:")
    result1, doc1 = search_article_by_id("형법 제1조")
    print(f"결과: {result1[:100]}...")
    
    # 2. 키워드 검색 테스트
    print("\n2. 키워드 검색 테스트:")
    result2, docs2 = retrieve("살인", filter="형법", k=2)
    print(f"결과: {result2[:100]}...")
    print(f"문서 수: {len(docs2)}")


if __name__ == "__main__":
    main() 