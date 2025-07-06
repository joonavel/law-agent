#!/usr/bin/env python3
"""
KMMLU 평가기
Criminal-Law 카테고리 데이터셋을 이용한 Agent System 평가
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
from tqdm import tqdm
import sys
import json

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
from src.agent.workflow import create_parent_graph
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# OpenAI Batch API용 프롬프트 정의
PARSING_TEMPLATE = """**Problem Core:**
{problem_core}

**Relevant Legal Provisions:**
{relevant_legal_provisions}

**Solution Points:**
{solution_points}
"""

SYSTEM_PROMPT = """You are an expert in Korean criminal law. Analyze the given multiple-choice question about Korean criminal law using the provided context. 

Instructions:
- Carefully read the question, all four options (A, B, C, D), and the context.
- Apply Korean criminal law principles to determine the correct answer
- Consider legal precedents, statutory provisions, and established legal interpretations
- Do not provide explanations or reasoning process
- Respond with only the letter of the correct answer (A, B, C, or D) AND CHOOSE only one answer even if the context indicates multiple answers
- If the context imply that there is no proper answer, Answer with your Knowledge of Korean criminal law.
- If you cannot find the correct answer or it is not valid question, respond with "IDK"
"""

USER_PROMPT = """Question: {question}

Options:
A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

Context:
{context}

Answer:"""


class KMMLUEvaluator:
    """KMMLU Criminal-Law 평가기"""
    
    def __init__(self, batch_size: int = 5, sleep_time: int = 5):
        """
        평가기 초기화
        
        Args:
            batch_size: 배치 크기 (기본값: 5)
            sleep_time: 배치 간 대기 시간 (초, 기본값: 5)
        """
        self.batch_size = batch_size
        self.sleep_time = sleep_time
        self.dataset = None
        self.graph = None
        self.batch_results = []
        
        # 파일 경로 설정
        self.data_dir = Path(project_root) / "data" / "batch"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 배치 관련 파일 경로
        self.input_batch_file = self.data_dir / "input_batch.jsonl"
        self.output_batch_file = self.data_dir / "output_batch.jsonl"
        self.input_id_file = self.data_dir / "input_id.txt"
        self.output_id_file = self.data_dir / "output_id.txt"
        
    def load_dataset(self):
        """KMMLU Criminal-Law 데이터셋 로드"""
        logger.info("KMMLU Criminal-Law 데이터셋 로드 중...")
        try:
            self.dataset = load_dataset("HAERAE-HUB/KMMLU", "Criminal-Law", split="test")
            logger.info(f"데이터셋 로드 완료: {len(self.dataset)}개 문제")
            return True
        except Exception as e:
            logger.error(f"데이터셋 로드 실패: {e}")
            return False
    
    def initialize_graph(self):
        """ParentGraph 초기화"""
        logger.info("ParentGraph 초기화 중...")
        try:
            self.graph = create_parent_graph()
            logger.info("ParentGraph 초기화 완료")
            return True
        except Exception as e:
            logger.error(f"ParentGraph 초기화 실패: {e}")
            return False
    
    def prepare_batch_inputs(self, batch_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        배치 입력 데이터 준비
        
        Args:
            batch_data: 배치 데이터
            
        Returns:
            Graph 입력 형식의 배치 데이터
        """
        batch_inputs = []
        
        for i, item in enumerate(batch_data):
            # 선택지 구성
            options = [
                item.get('A', ''),
                item.get('B', ''),
                item.get('C', ''),
                item.get('D', '')
            ]
            
            # Graph 입력 형식으로 변환
            graph_input = {
                "user_question": item.get('question', ''),
                "user_options": options,
                "thread_id": f"kmmlu_test_{i}"
            }
            
            batch_inputs.append(graph_input)
        
        return batch_inputs
    
    def evaluate_batch(self, start_idx: int = 0, end_idx: int = None) -> List[Dict[str, Any]]:
        """
        배치 단위로 평가 실행
        
        Args:
            start_idx: 시작 인덱스
            end_idx: 종료 인덱스 (None이면 전체 데이터셋)
            
        Returns:
            평가 결과 리스트
        """
        if not self.dataset:
            logger.error("데이터셋이 로드되지 않았습니다.")
            return []
        
        if not self.graph:
            logger.error("ParentGraph가 초기화되지 않았습니다.")
            return []
        
        # 평가 범위 설정
        if end_idx is None:
            end_idx = len(self.dataset)
        
        logger.info(f"배치 평가 시작: 인덱스 {start_idx}~{end_idx} (총 {end_idx - start_idx}개 문제)")
        logger.info(f"배치 크기: {self.batch_size}, 배치 간 대기 시간: {self.sleep_time}초")
        
        self.batch_results = []
        
        # 배치 단위로 처리
        for idx in tqdm(range(start_idx, end_idx, self.batch_size), desc="KMMLU 평가 진행"):
            batch_end_idx = min(idx + self.batch_size, end_idx)
            
            # 현재 배치 데이터 추출
            batch_data = [self.dataset[i] for i in range(idx, batch_end_idx)]
            
            logger.info(f"배치 {idx//self.batch_size + 1} 처리 중: 인덱스 {idx}~{batch_end_idx-1}")
            
            try:
                # 배치 입력 준비
                batch_inputs = self.prepare_batch_inputs(batch_data)
                
                # 실제 인덱스로 thread_id 재설정
                for i, batch_input in enumerate(batch_inputs):
                    batch_input["thread_id"] = f"kmmlu_test_{idx + i}"
                
                # 그래프 배치 실행
                batch_result = self.graph.batch(
                    inputs=batch_inputs, 
                    config={"recursion_limit": 25}
                )
                # 결과 저장 (원본 데이터와 함께)
                for i, (original, result) in enumerate(zip(batch_data, batch_result)):
                    combined_result = {
                        "index": idx + i,
                        "original_data": original,
                        "agent_result": result
                    }
                    self.batch_results.append(combined_result)
                
                logger.info(f"배치 {idx//self.batch_size + 1} 완료: {len(batch_result)}개 결과")
                
            except Exception as e:
                logger.error(f"배치 {idx//self.batch_size + 1} 처리 실패: {e}")
                # 실패한 배치도 기록 (디버깅용)
                for i, original in enumerate(batch_data):
                    failed_result = {
                        "index": idx + i,
                        "original_data": original,
                        "agent_result": None,
                        "error": str(e)
                    }
                    self.batch_results.append(failed_result)
            
            # 배치 간 대기 (API 요청 제한 고려)
            if idx + self.batch_size < end_idx:
                logger.info(f"{self.sleep_time}초 대기 중...")
                time.sleep(self.sleep_time)
        
        logger.info(f"배치 평가 완료: 총 {len(self.batch_results)}개 결과")
        return self.batch_results
    
    def run_evaluation(self, start_idx: int = 0, end_idx: int = None, test_limit: int = None) -> List[Dict[str, Any]]:
        """
        전체 평가 프로세스 실행
        
        Args:
            start_idx: 시작 인덱스
            end_idx: 종료 인덱스 (None이면 전체 데이터셋)
            test_limit: 테스트용 데이터 개수 제한 (None이면 전체 데이터 사용)
            
        Returns:
            평가 결과 리스트
        """
        # 1. 데이터셋 로드
        if not self.load_dataset():
            return []
        
        # 2. 그래프 초기화
        if not self.initialize_graph():
            return []
        
        # 테스트 제한 적용
        if test_limit is not None:
            end_idx = min(test_limit, len(self.dataset))
            logger.info(f"테스트 제한 적용: {end_idx}개 데이터 사용")
        
        # 3. 배치 평가 실행
        results = self.evaluate_batch(start_idx, end_idx)
        
        return results

    def create_batch_file_from_results(self, evaluation_results: List[Dict], output_file: str = "input_batch.jsonl") -> str:
        """
        run_evaluation 결과를 바탕으로 OpenAI Batch API용 파일 생성
        
        Args:
            evaluation_results: run_evaluation에서 얻은 결과 리스트
            output_file: 출력 파일명
            
        Returns:
            생성된 파일 경로
        """
        logger.info(f"평가 결과를 바탕으로 배치 파일 생성: {output_file}")
        
        if not evaluation_results:
            logger.error("평가 결과가 없습니다")
            return ""
        
        full_path = self.data_dir / output_file
        
        with open(full_path, 'w', encoding='utf-8') as f:
            for idx, result in enumerate(evaluation_results):
                context = None
                
                # 원본 데이터에서 질문과 선택지 가져오기
                original_data = result.get('original_data', {})
                question = original_data.get('question', '')
                options = [
                    original_data.get('A', ''),
                    original_data.get('B', ''), 
                    original_data.get('C', ''),
                    original_data.get('D', '')
                ]
                
                # parent_graph 결과가 유효한 경우 context 생성
                try:
                    agent_result = result.get('agent_result')
                    if agent_result and agent_result.get('question_validation') and agent_result.get('result'):
                        question_validation = agent_result['question_validation']
                        if hasattr(question_validation, 'is_valid') and question_validation.is_valid:
                            
                            problem_core = agent_result['result'].problem_core
                            relevant_legal_provisions = '\n'.join([f"- {item}" for item in agent_result['result'].relevant_legal_provisions])
                            solution_points = '\n'.join([f"- {item}" for item in agent_result['result'].solution_points])
                            
                            context = PARSING_TEMPLATE.format(
                                problem_core=problem_core,
                                relevant_legal_provisions=relevant_legal_provisions,
                                solution_points=solution_points
                            )
                            logger.info(f"문제 {idx+1}: Parent Graph 결과 사용")
                        else:
                            logger.info(f"문제 {idx+1}: 유효하지 않은 결과, fallback 사용")
                    else:
                        logger.info(f"문제 {idx+1}: 에이전트 결과 없음, fallback 사용")
                except Exception as e:
                    logger.warning(f"문제 {idx+1}: context 생성 실패 ({e}), fallback 사용")
                
                # context가 None이면 fallback 문자열 사용
                if context is None:
                    context = "Answer based on your knowledge of Korean criminal law."
                
                # 프롬프트 포맷팅
                formatted_prompt = USER_PROMPT.format(
                    question=question,
                    option_a=options[0],
                    option_b=options[1],
                    option_c=options[2],
                    option_d=options[3],
                    context=context
                )
                
                # Responses API 방식의 태스크 생성
                task = {
                    "custom_id": f"q{idx+1:03d}",
                    "method": "POST",
                    "url": "/v1/responses",
                    "body": {
                        "model": "gpt-4o-mini",
                        "instructions": SYSTEM_PROMPT,
                        "input": formatted_prompt,
                        "temperature": 0,
                        "max_tool_calls": 10,
                    }
                }
                
                f.write(json.dumps(task, ensure_ascii=False) + '\n')
        
        logger.info(f"배치 파일 생성 완료: {full_path}")
        logger.info(f"총 {len(evaluation_results)}개 문제 처리됨")
        
        return str(full_path)

    def create_batch(self, batch_file_path: str) -> Dict[str, Any]:
        """
        배치 파일을 업로드하고 배치 작업 생성
        
        Args:
            batch_file_path: 업로드할 배치 파일 경로
            
        Returns:
            배치 작업 정보 딕셔너리
        """
        try:
            client = OpenAI()
            
            logger.info(f"배치 파일 업로드 시작: {batch_file_path}")
            
            # 1. 파일 업로드
            with open(batch_file_path, "rb") as file:
                batch_input_file = client.files.create(
                    file=file,
                    purpose="batch"
                )
            
            logger.info(f"배치 파일 업로드 완료: {batch_input_file.id}")
            
            # 2. 배치 작업 생성
            batch_job = client.batches.create(
                input_file_id=batch_input_file.id,
                endpoint="/v1/responses",
                completion_window="24h",
                metadata={
                    "description": "Korean criminal law multiple choice questions",
                    "purpose": "legal_qa_evaluation"
                }
            )
            
            logger.info(f"배치 작업 생성 완료: {batch_job.id}")
            logger.info(f"상태: {batch_job.status}")
            
            # 3. 배치 ID를 input_id.txt에 저장
            with open(self.input_id_file, 'w', encoding='utf-8') as f:
                f.write(batch_job.id)
            logger.info(f"배치 ID 저장 완료: {self.input_id_file}")
            
            # 배치 작업 정보 반환
            batch_info = {
                "batch_id": batch_job.id,
                "status": batch_job.status,
                "input_file_id": batch_input_file.id,
                "created_at": batch_job.created_at,
                "completion_window": batch_job.completion_window,
                "metadata": batch_job.metadata
            }
            
            return batch_info
            
        except Exception as e:
            logger.error(f"배치 작업 생성 실패: {e}")
            return {}

    def run_full_evaluation_with_monitoring(self) -> Optional[Dict[str, Any]]:
        """
        전체 워크플로우 실행 (사용자 제시 로직)
        1단계: 배치 업로드 - 새 배치 작업 생성 → 배치 ID를 input_id.txt에 저장
        2단계: 평가 로직 - input_id.txt의 배치 ID로 상태 모니터링
        3단계: 평가 시작 전 검증 - input_id.txt와 output_id.txt 존재 & 값 확인
        
        Returns:
            평가 결과 딕셔너리
        """
        logger.info("🚀 전체 워크플로우 시작")
        
        # 1단계: 배치 업로드
        logger.info("1️⃣ 배치 업로드 단계")
        logger.info("   - Parent Graph로 평가 실행 (테스트용 10개 데이터)")
        evaluation_results = self.run_evaluation(test_limit=10)
        if not evaluation_results:
            logger.error("평가 실행 실패")
            return None
        
        logger.info("   - 평가 결과를 바탕으로 배치 파일 생성")
        batch_file_path = self.create_batch_file_from_results(evaluation_results)
        if not batch_file_path:
            logger.error("배치 파일 생성 실패")
            return None
        
        logger.info("   - 배치 작업 생성 및 업로드")
        batch_info = self.create_batch(batch_file_path)
        if not batch_info:
            logger.error("배치 작업 생성 실패")
            return None
        
        logger.info(f"   - 배치 ID 저장 완료: {batch_info['batch_id']}")
        
        # 2단계: 평가 로직 (모니터링)
        logger.info("2️⃣ 평가 로직 단계")
        
        # input_id.txt에 있는 배치 ID로 모니터링
        if self.input_id_file.exists():
            with open(self.input_id_file, 'r', encoding='utf-8') as f:
                batch_id = f.read().strip()
            
            logger.info(f"   - 배치 ID로 상태 모니터링: {batch_id}")
            batch_status = self.monitor_batch(batch_id)
            
            if batch_status == "completed":
                logger.info("   - 상태: completed → output 파일 다운로드")
                success = self.download_batch_output(batch_id)
                if success:
                    logger.info("   - 배치 출력 파일 다운로드 완료")
                else:
                    logger.warning("   - 배치 출력 파일 다운로드 실패")
            else:
                logger.info(f"   - 상태: {batch_status} → 기존 output_batch.jsonl로 평가 진행")
        else:
            logger.warning("   - input_id.txt 파일이 없음")
        
        # 3단계: 평가 시작 전 검증
        logger.info("3️⃣ 평가 시작 전 검증 단계")
        
        # input_id.txt와 output_id.txt 파일 존재 확인
        if not self.input_id_file.exists():
            logger.error("   - input_id.txt 파일이 없습니다")
            return None
        
        if not self.output_id_file.exists():
            logger.warning("   - output_id.txt 파일이 없습니다 (배치가 완료되지 않았을 수 있음)")
            # output_id.txt가 없어도 평가는 진행
        
        # 배치 ID 검증
        id_match = self.verify_batch_ids()
        if not id_match:
            logger.warning("   - 배치 ID 불일치 또는 파일 없음")
        
        # 4단계: 배치 출력 파일로 평가 실행
        logger.info("4️⃣ 배치 출력 파일로 평가 실행")
        results = self.evaluate_from_batch_output()
        
        return results

    def verify_batch_ids(self) -> bool:
        """
        배치 ID 검증
        input_id.txt와 output_id.txt의 배치 ID가 일치하는지 확인
        
        Returns:
            ID가 일치하면 True, 아니면 False
        """
        try:
            # 파일 존재 확인
            if not self.input_id_file.exists():
                logger.warning("input_id.txt 파일이 없습니다")
                return False
            
            if not self.output_id_file.exists():
                logger.warning("output_id.txt 파일이 없습니다")
                return False
            
            # ID 읽기
            with open(self.input_id_file, 'r', encoding='utf-8') as f:
                input_id = f.read().strip()
            
            with open(self.output_id_file, 'r', encoding='utf-8') as f:
                output_id = f.read().strip()
            
            # ID 비교
            if input_id == output_id:
                logger.info(f"✅ 배치 ID 일치: {input_id}")
                return True
            else:
                logger.warning(f"⚠️  배치 ID 불일치 - 입력: {input_id}, 출력: {output_id}")
                logger.warning("출력 값은 입력 값으로부터 나온게 아니므로 평가 결과는 믿을 수 없다")
                return False
                
        except Exception as e:
            logger.error(f"배치 ID 검증 실패: {e}")
            return False

    def monitor_batch(self, batch_id: str) -> str:
        """
        배치 상태 모니터링
        
        Args:
            batch_id: 배치 ID
            
        Returns:
            배치 상태 (validating, in_progress, completed, failed, etc.)
        """
        try:
            client = OpenAI()
            batch = client.batches.retrieve(batch_id)
            
            logger.info(f"배치 상태: {batch.status}")
            return batch.status
            
        except Exception as e:
            logger.error(f"배치 상태 확인 실패: {e}")
            return "error"

    def download_batch_output(self, batch_id: str) -> bool:
        """
        배치 출력 파일 다운로드
        
        Args:
            batch_id: 배치 ID
            
        Returns:
            다운로드 성공 여부
        """
        try:
            client = OpenAI()
            batch = client.batches.retrieve(batch_id)
            
            if batch.status != "completed":
                logger.error(f"배치가 완료되지 않았습니다. 상태: {batch.status}")
                return False
            
            if not batch.output_file_id:
                logger.error("출력 파일 ID가 없습니다")
                return False
            
            # 출력 파일 다운로드
            file_response = client.files.content(batch.output_file_id)
            
            # 파일 저장
            with open(self.output_batch_file, 'wb') as f:
                f.write(file_response.content)
            
            # output_id.txt에 배치 ID 저장
            with open(self.output_id_file, 'w', encoding='utf-8') as f:
                f.write(batch_id)
            
            logger.info(f"배치 출력 파일 다운로드 완료: {self.output_batch_file}")
            return True
            
        except Exception as e:
            logger.error(f"배치 출력 파일 다운로드 실패: {e}")
            return False

    def get_questions_and_results(self, input_file: str, output_file: str):
        """
        사용자가 제공한 로직을 기반으로 질문과 결과를 딕셔너리로 매핑
        
        Args:
            input_file: 입력 파일 경로
            output_file: 출력 파일 경로
            
        Returns:
            questions, results 딕셔너리
        """
        questions = {}
        with open(input_file, "r", encoding='utf-8') as f:
            for line in f:
                question = json.loads(line)
                questions[question["custom_id"]] = question["body"]

        results = {}
        with open(output_file, "r", encoding='utf-8') as f:
            for line in f:
                result = json.loads(line)
                # Responses API 응답 형태에 맞게 수정 (사용자 제공 로직 기반)
                try:
                    content = result['response']['body']['output'][0]['content'][0]['text'].strip()
                    results[result["custom_id"]] = content
                except (KeyError, IndexError, TypeError):
                    results[result["custom_id"]] = ""
        
        return questions, results

    def evaluate_results(self, ds, results):
        """
        사용자가 제공한 평가 로직
        
        Args:
            ds: 데이터셋
            results: 결과 딕셔너리
            
        Returns:
            correct, fails, wrong_preds
        """
        mapping_dict = {"A": 1, "B": 2, "C": 3, "D": 4}
        correct = 0
        fails = []
        wrong_preds = []
        
        for idx in range(len(ds)):
            custom_id = f"q{idx+1:03d}"
            y_true = ds[idx]['answer']
            y_pred = mapping_dict.get(results.get(custom_id, ''), 0)
            
            if y_pred:
                if y_true == y_pred:
                    correct += 1
                else:
                    wrong_preds.append(idx)
            else:
                fails.append(idx)

        print(f"correct: {correct}, fails: {len(fails)}, wrong_preds: {len(wrong_preds)}")
        print(f"accuracy: {correct / len(ds)}")

        return correct, fails, wrong_preds

    def evaluate_from_batch_output(self) -> Optional[Dict[str, Any]]:
        """
        사용자가 제공한 로직을 기반으로 배치 출력 파일 평가
        
        Returns:
            평가 결과 딕셔너리
        """
        try:
            if not self.output_batch_file.exists():
                logger.error(f"배치 출력 파일이 없습니다: {self.output_batch_file}")
                return None
            
            # input_batch.jsonl 파일 경로
            input_file = str(self.input_batch_file)
            if not self.input_batch_file.exists():
                logger.error(f"입력 배치 파일이 없습니다: {self.input_batch_file}")
                return None
            
            # KMMLU 데이터셋 로드
            if not self.dataset:
                if not self.load_dataset():
                    logger.error("데이터셋 로드 실패")
                    return None
            
            # 사용자가 제공한 로직 사용
            questions, results = self.get_questions_and_results(input_file, str(self.output_batch_file))
            correct, fails, wrong_preds = self.evaluate_results(self.dataset, results)
            
            # 결과 정리
            total_count = len(self.dataset)
            correct_count = correct
            accuracy = correct / total_count if total_count > 0 else 0
            
            evaluation_result = {
                'total_count': total_count,
                'correct_count': correct_count,
                'accuracy': accuracy,
                'fails': fails,
                'wrong_preds': wrong_preds,
                'questions': questions,
                'results': results
            }
            
            logger.info(f"배치 출력 파일 평가 완료: {total_count}개 문제, {correct_count}개 정답, {accuracy:.2%} 정확도")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"배치 출력 파일 평가 실패: {e}")
            return None

    def get_results(self) -> List[Dict[str, Any]]:
        """평가 결과 반환"""
        return self.batch_results
    
    def print_summary(self):
        """평가 결과 요약 출력"""
        if not self.batch_results:
            print("평가 결과가 없습니다.")
            return
        
        total_count = len(self.batch_results)
        success_count = sum(1 for r in self.batch_results if r.get('agent_result') is not None)
        failed_count = total_count - success_count
        
        print(f"\n{'='*60}")
        print(f"🎯 KMMLU 평가 결과 요약")
        print(f"{'='*60}")
        print(f"📊 총 문제 수: {total_count}")
        print(f"✅ 성공: {success_count}")
        print(f"❌ 실패: {failed_count}")
        print(f"📈 성공률: {success_count/total_count*100:.1f}%")
        
        if failed_count > 0:
            print(f"\n❌ 실패한 문제 인덱스:")
            failed_indices = [r['index'] for r in self.batch_results if r.get('agent_result') is None]
            print(f"   {failed_indices}")


def main():
    """메인 실행 함수"""
    evaluator = KMMLUEvaluator(batch_size=5, sleep_time=10)
    
    # 제안된 워크플로우로 전체 평가 실행
    print("🚀 KMMLU 평가 시작 (전체 워크플로우)")
    results = evaluator.run_full_evaluation_with_monitoring()
    
    if results:
        print(f"\n✅ 전체 평가 완료!")
        print(f"총 문제 수: {results['total_count']}")
        print(f"정답: {results['correct_count']}")
        print(f"정확도: {results['accuracy']:.2%}")
        
        # 실패 및 틀린 답변 요약
        print(f"\n📊 실패: {len(results['fails'])}개, 틀린 답변: {len(results['wrong_preds'])}개")
    else:
        print("❌ 평가 실패")
    
    return results


if __name__ == "__main__":
    results = main() 