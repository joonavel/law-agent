#!/usr/bin/env python3
"""
통합 워크플로우 테스트 스크립트
ParentGraph와 SubGraph 통합 테스트
"""

import logging
from pathlib import Path
import traceback
import uuid

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agent.workflow import create_parent_graph

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_integrated_workflow():
    """통합 워크플로우 테스트 실행"""
    print("=" * 60)
    print("🔍 통합 워크플로우 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. ParentGraph 생성
        print("\n1️⃣ ParentGraph 생성 중...")
        graph = create_parent_graph()
        print("✅ ParentGraph 생성 완료")
        
        # 2. 테스트 케이스들
        test_cases = [
            {
                "name": "유효한 살인 및 시체유기 사건",
                "question": "A가 B를 살해한 후 시체를 유기했다. 이 경우 A에게 적용될 수 있는 죄명은?",
                "options": [
                    "살인죄와 시체유기죄",
                    "살인죄만 적용",
                    "시체유기죄만 적용",
                    "살인죄와 시체손괴죄"
                ]
            },
            {
                "name": "유효한 형법 조문 질문",
                "question": "형법 제1조에 규정된 죄형법정주의에 대한 설명으로 옳은 것은?",
                "options": [
                    "범죄와 형벌은 법률에 의해서만 정할 수 있다",
                    "범죄와 형벌은 판사가 결정할 수 있다",
                    "범죄와 형벌은 검사가 결정할 수 있다",
                    "범죄와 형벌은 경찰이 결정할 수 있다"
                ]
            },
            {
                "name": "무효한 질문 (선택지가 기호만 있음)",
                "question": "다음 중 옳은 것(○)과 옳지 않은 것(×)을 바르게 연결한 것은?",
                "options": [
                    "○×○○",
                    "×○×○",
                    "○○××",
                    "××○○"
                ]
            }
        ]
        
        # 3. 각 테스트 케이스 실행
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i+1}️⃣ 테스트: {test_case['name']}")
            print(f"문제: {test_case['question'][:50]}...")
            print(f"선택지 수: {len(test_case['options'])}")
            print("-" * 50)
            
            try:
                # 테스트 입력 생성
                test_input = {
                    "thread_id": f"test_{uuid.uuid4().hex[:8]}",
                    "user_question": test_case['question'],
                    "user_options": test_case['options']
                }
                
                # 워크플로우 실행
                result = graph.invoke(test_input)
                
                # 결과 출력
                print(f"📝 스레드 ID: {result.get('thread_id')}")
                
                # 유효성 검사 결과
                validation = result.get('question_validation')
                if validation:
                    print(f"✅ 유효성 검사: {'통과' if validation.is_valid == 1 else '실패'}")
                    if validation.reason:
                        print(f"   실패 사유: {validation.reason}")
                else:
                    print("❌ 유효성 검사 결과 없음")
                
                # 문제 분류 결과
                classification = result.get('problem_classification')
                if classification:
                    print(f"📊 문제 분류: {', '.join(classification.classifications)}")
                    print(f"   분류 근거: {classification.reasoning[:100]}...")
                else:
                    print("📊 문제 분류: 미실행")
                
                # 최종 분석 결과
                final_result = result.get('result')
                if final_result:
                    print(f"🎯 문제 핵심: {final_result.problem_core}")
                    print(f"📋 관련 법령: {len(final_result.relevant_legal_provisions)}개")
                    for j, provision in enumerate(final_result.relevant_legal_provisions[:3], 1):
                        print(f"   {j}. {provision[:80]}...")
                    print(f"💡 해결 포인트: {len(final_result.solution_points)}개")
                    for j, point in enumerate(final_result.solution_points[:3], 1):
                        print(f"   {j}. {point[:80]}...")
                else:
                    print("🎯 최종 결과: 없음 (유효성 검사 실패 또는 오류)")
                
                # Fallback 처리 여부 확인 (로그 출력에서 확인 가능)
                print("📝 Fallback 처리 여부는 위 로그에서 확인 가능")
                
                print("✅ 테스트 완료")
                
            except Exception as e:
                print(f"❌ 테스트 실패: {e}")
                logger.error(f"테스트 케이스 {i} 실패: {traceback.format_exc()}")
        
        print(f"\n🎉 통합 워크플로우 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 통합 워크플로우 테스트 실패: {e}")
        logger.error(f"통합 워크플로우 테스트 전체 실패: {traceback.format_exc()}")
        raise


def test_individual_nodes():
    """개별 노드 테스트"""
    print("\n" + "=" * 60)
    print("🔧 개별 노드 테스트 시작")
    print("=" * 60)
    
    try:
        from src.agent.workflow import (
            validate_question, 
            classify_problem, 
            handle_failure,
            make_validation_chain,
            make_classification_chain,
            make_fallback_handling_chain
        )
        
        # 테스트 상태 생성
        test_state = {
            "thread_id": "node_test_001",
            "user_question": "A가 B를 살해한 후 시체를 유기했다. 이 경우 A에게 적용될 수 있는 죄명은?",
            "user_options": [
                "살인죄와 시체유기죄",
                "살인죄만 적용",
                "시체유기죄만 적용",
                "살인죄와 시체손괴죄"
            ]
        }
        
        # 1. 유효성 검사 노드 테스트
        print("\n1️⃣ 유효성 검사 노드 테스트")
        validation_result = validate_question(test_state)
        print(f"   결과: {validation_result}")
        
        # 2. 문제 분류 노드 테스트
        print("\n2️⃣ 문제 분류 노드 테스트")
        classification_result = classify_problem(test_state)
        print(f"   결과: {classification_result}")
        
        # 3. 실패 처리 노드 테스트
        print("\n3️⃣ 실패 처리 노드 테스트")
        test_state["question_validation"] = type('obj', (object,), {'is_valid': 0, 'reason': '테스트 실패'})()
        failure_result = handle_failure(test_state)
        print(f"   결과: {failure_result}")
        
        # 4. Fallback 체인 테스트
        print("\n4️⃣ Fallback 처리 체인 테스트")
        try:
            fallback_chain = make_fallback_handling_chain()
            test_history = "user: A가 B를 살해한 후 시체를 유기했다.\nassistant: 형법 제250조 살인죄와 형법 제161조 시체유기죄가 적용됩니다."
            fallback_result = fallback_chain.invoke({"history_text": test_history})
            print(f"   결과: {fallback_result}")
        except Exception as e:
            print(f"   Fallback 체인 테스트 실패: {e}")
        
        print("✅ 개별 노드 테스트 완료")
        
    except Exception as e:
        print(f"❌ 개별 노드 테스트 실패: {e}")
        logger.error(f"개별 노드 테스트 실패: {traceback.format_exc()}")


def main():
    """메인 함수"""
    # 통합 워크플로우 테스트
    test_integrated_workflow()
    
    # 개별 노드 테스트
    test_individual_nodes()


if __name__ == "__main__":
    main() 