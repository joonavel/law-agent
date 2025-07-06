#!/usr/bin/env python3
"""
data/batch의 input_id.txt를 확인하고 배치 상태를 모니터링하여 최종 평가를 진행하는 스크립트

Usage:
    python scripts/evaluate_batch_results.py
"""

import os
import sys
import logging
import time
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
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
        logger.info("🔍 KMMLU 배치 결과 평가 시작")
        
        # 1. KMMLUEvaluator 초기화
        evaluator = KMMLUEvaluator()
        
        # 2. input_id.txt 확인
        input_id_file = evaluator.data_dir / "input_id.txt"
        
        if not input_id_file.exists():
            logger.error(f"input_id.txt 파일이 없습니다: {input_id_file}")
            logger.error("먼저 create_batch_upload.py를 실행하여 배치를 생성하세요.")
            return False
        
        batch_id = input_id_file.read_text().strip()
        logger.info(f"📋 배치 ID 확인: {batch_id}")
        
        # 3. 배치 상태 모니터링
        logger.info("⏳ 배치 상태 모니터링 시작...")
        logger.info("   - 배치 처리 완료까지 최대 10분 소요될 수 있습니다")
        logger.info("   - 상태 체크 간격: 30초")
        
        # TODO 제출시 600초로 변경
        max_wait_time = 60  # 10분
        check_interval = 30  # 30초
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                # 배치 상태 확인
                batch_status = evaluator.monitor_batch(batch_id)
                
                if not batch_status:
                    logger.error("배치 상태 확인 실패")
                    return False
                
                logger.info(f"📊 배치 상태: {batch_status}")
                
                if batch_status == "completed":
                    logger.info("✅ 배치 처리 완료!")
                    break
                elif batch_status == "failed":
                    logger.error("❌ 배치 처리 실패")
                    return False
                elif batch_status == "expired":
                    logger.error("⏰ 배치 처리 시간 만료")
                    return False
                else:
                    logger.info(f"⏳ 대기 중... (경과 시간: {elapsed_time}초)")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
            except Exception as e:
                logger.warning(f"상태 확인 중 오류: {e}")
                time.sleep(check_interval)
                elapsed_time += check_interval
        
        if elapsed_time >= max_wait_time:
            logger.warning("⏰ 최대 대기 시간 초과")
            logger.info("배치가 아직 완료되지 않았지만 기존 결과로 평가를 진행합니다.")
        
        # 4. 배치 결과 다운로드 (완료된 경우)
        if batch_status == "completed":
            logger.info("📥 배치 결과 다운로드 중...")
            
            download_success = evaluator.download_batch_output(batch_id)
            
            if download_success:
                logger.info("✅ 배치 결과 다운로드 완료")
                
                # output_id.txt에 배치 ID 저장
                output_id_file = evaluator.data_dir / "output_id.txt"
                output_id_file.write_text(batch_id)
                logger.info(f"💾 출력 배치 ID 저장: {output_id_file}")
            else:
                logger.warning("⚠️ 배치 결과 다운로드 실패, 기존 결과로 평가 진행")
        
        # 5. 최종 평가 실행
        logger.info("📊 최종 평가 실행 중...")
        
        # 배치 출력 파일로 평가
        results = evaluator.evaluate_from_batch_output()
        
        if not results:
            logger.error("평가 실행 실패")
            return False
        
        # 6. 결과 출력
        logger.info("=" * 60)
        logger.info("🎉 KMMLU 평가 완료!")
        logger.info(f"📊 총 문제 수: {results.get('total_count', 0)}")
        logger.info(f"✅ 정답 수: {results.get('correct_count', 0)}")
        logger.info(f"❌ 오답 수: {len(results.get('wrong_preds', []))}")
        logger.info(f"⚠️ 실패 수: {len(results.get('fails', []))}")
        logger.info(f"🎯 정확도: {results.get('accuracy', 0):.2%}")
        logger.info("=" * 60)
        
        # 7. 결과 상세 정보 출력
        if results.get('accuracy', 0) > 0:
            logger.info("📈 평가 결과 상세:")
            logger.info(f"   - 정답률: {results.get('accuracy', 0):.4f}")
            logger.info(f"   - 배치 ID: {batch_id}")
            logger.info(f"   - 출력 파일: {evaluator.data_dir / 'output_batch.jsonl'}")
        
        return True
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 