#!/usr/bin/env python3
"""
법령 데이터 수집 및 파싱 스크립트
웹 스크래핑 -> 파싱 -> 저장까지의 전체 파이프라인
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# 프로젝트 루트 디렉터리를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collector.web_scraper import LawScraper, LAW_URL_DICT
from src.data_collector.data_parser import LawParser

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_chunks_to_json(chunks: List[Dict[str, Any]], output_path: Path) -> None:
    """
    청킹된 데이터를 JSON 파일로 저장
    
    Args:
        chunks: 청킹된 법령 데이터
        output_path: 저장할 파일 경로
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"저장 완료: {output_path} ({len(chunks)}개 조문)")
    except Exception as e:
        logger.error(f"저장 실패: {output_path} - {e}")
        raise


def main():
    """메인 함수"""
    logger.info("=" * 50)
    logger.info("법령 데이터 수집 및 파싱 시작")
    logger.info("=" * 50)
    
    # 디렉터리 생성
    data_raw_dir = project_root / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. 웹 스크래핑 초기화
    logger.info("1. 웹 스크래핑 모듈 초기화")
    scraper = LawScraper(headless=True)
    
    # 2. 파싱 모듈 초기화
    logger.info("2. 파싱 모듈 초기화")
    parser = LawParser()
    
    # 3. 법령별 데이터 수집 및 파싱
    logger.info("3. 법령 데이터 수집 및 파싱 시작")
    logger.info(f"처리할 법령 수: {len(LAW_URL_DICT)}")
    
    total_chunks = 0
    success_count = 0
    
    for law_name, url in LAW_URL_DICT.items():
        try:
            logger.info(f"처리 중: {law_name}")
            
            # 스크래핑
            logger.info(f"  - 스크래핑: {law_name}")
            result = scraper.scrape_law_content(url)
            
            if not result:
                logger.warning(f"  - 스크래핑 실패: {law_name}")
                continue
                
            main_rules, _ = result
            logger.info(f"  - 스크래핑 성공: {law_name} (본문: {len(main_rules)})")
            
            # 파싱
            logger.info(f"  - 파싱: {law_name}")
            chunks = parser.chunk_by_article(law_name, main_rules)
            
            
            if not chunks:
                logger.warning(f"  - 파싱 실패: {law_name}")
                continue
                
            logger.info(f"  - 파싱 성공: {law_name} ({len(chunks)}개 조문)")
            
            # 저장
            output_file = data_raw_dir / f"{law_name}.json"
            save_chunks_to_json(chunks, output_file)
            
            total_chunks += len(chunks)
            success_count += 1
            
            logger.info(f"  - 완료: {law_name} ✓")
            
        except Exception as e:
            logger.error(f"  - 오류 발생: {law_name} - {e}")
            continue
    
    # 4. 결과 요약
    logger.info("=" * 50)
    logger.info("처리 결과 요약")
    logger.info("=" * 50)
    logger.info(f"총 법령 수: {len(LAW_URL_DICT)}")
    logger.info(f"성공 법령 수: {success_count}")
    logger.info(f"실패 법령 수: {len(LAW_URL_DICT) - success_count}")
    logger.info(f"총 조문 수: {total_chunks}")
    logger.info(f"저장 위치: {data_raw_dir}")
    
    # 저장된 파일 목록 출력
    saved_files = list(data_raw_dir.glob("*.json"))
    logger.info(f"저장된 파일 수: {len(saved_files)}")
    for file in saved_files:
        logger.info(f"  - {file.name}")
    
    logger.info("=" * 50)
    logger.info("법령 데이터 수집 및 파싱 완료")
    logger.info("=" * 50)


if __name__ == "__main__":
    main() 