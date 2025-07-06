#!/usr/bin/env python3
"""
KMMLU 전체 데이터셋을 처리하여 OpenAI Batch API용 파일을 생성하고 업로드하는 스크립트

Usage:
    python scripts/create_batch_upload.py
"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.kmmlu_evaluator import KMMLUEvaluator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """메인 실행 함수"""
    try:
        logger.info("🚀 KMMLU 배치 파일 생성 및 업로드 시작")
        
        # 1. KMMLUEvaluator 초기화
        evaluator = KMMLUEvaluator()
        
        # 2. 데이터셋 로드
        logger.info("📊 KMMLU 데이터셋 로드 중...")
        if not evaluator.load_dataset():
            logger.error("데이터셋 로드 실패")
            return False
        
        # 3. 그래프 초기화
        logger.info("🔧 Parent Graph 초기화 중...")
        if not evaluator.initialize_graph():
            logger.error("그래프 초기화 실패")
            return False
        
        # 4. 전체 데이터셋으로 평가 실행 (200개 전체)
        logger.info("🎯 전체 데이터셋으로 Parent Graph 평가 실행 중...")
        logger.info("   - 총 200개 데이터 처리 예정")
        logger.info("   - 예상 소요 시간: 약 20분")
        
        # TODO 제출시 test_limit=None으로 변경
        evaluation_results = evaluator.run_evaluation(test_limit=5)
        
        if not evaluation_results:
            logger.error("평가 실행 실패")
            return False
        
        logger.info(f"✅ 평가 완료: {len(evaluation_results)}개 결과 생성")
        
        # 5. 배치 파일 생성
        logger.info("📝 배치 파일 생성 중...")
        batch_file_path = evaluator.create_batch_file_from_results(
            evaluation_results, 
            output_file="input_batch.jsonl"
        )
        
        if not batch_file_path:
            logger.error("배치 파일 생성 실패")
            return False
        
        logger.info(f"✅ 배치 파일 생성 완료: {batch_file_path}")
        
        # 6. OpenAI에 업로드 및 배치 작업 생성
        logger.info("☁️  OpenAI에 배치 파일 업로드 및 배치 작업 생성 중...")
        batch_info = evaluator.create_batch(batch_file_path)
        
        if not batch_info:
            logger.error("배치 업로드 및 작업 생성 실패")
            return False
        
        batch_id = batch_info.get('batch_id')
        logger.info(f"✅ 배치 업로드 및 작업 생성 완료: {batch_id}")
        logger.info(f"📊 배치 상태: {batch_info.get('status')}")
        
        # 배치 ID는 create_batch 내부에서 이미 저장됨
        logger.info(f"💾 배치 ID가 이미 저장됨: {evaluator.input_id_file}")
        
        # 8. 결과 요약
        logger.info("=" * 60)
        logger.info("🎉 배치 파일 생성 및 업로드 완료!")
        logger.info(f"📁 배치 파일: {batch_file_path}")
        logger.info(f"🆔 배치 ID: {batch_id}")
        logger.info(f"💾 ID 저장 위치: {evaluator.input_id_file}")
        logger.info(f"📊 처리된 문제 수: {len(evaluation_results)}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 