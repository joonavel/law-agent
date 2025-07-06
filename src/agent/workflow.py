"""
LangGraph 함수형 패턴 기반 법령 분석 워크플로우
ParentGraph와 SubGraph 통합 구현
"""

import logging
from typing import List, Optional, Annotated, Literal
from pathlib import Path
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.errors import GraphRecursionError
from dotenv import load_dotenv

import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agent.rag_retriever import get_rag_tools

# .env 파일 로드
env_path = project_root / ".env"
load_dotenv(env_path)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 상태 정의 ====================

class InputValidationResult(BaseModel):
    '''
    validation result of the input question and choices.
    '''
    is_valid: int = Field(description="1 if the question and choices are appropriate, 0 otherwise")
    reason: Optional[str] = Field(description="Reason for why the question and choices are invalid")


class ProblemClassificationResult(BaseModel):
    """형법 문제 분류 결과"""
    classifications: List[str] = Field(description="List of problem types that the problem belongs to")
    reasoning: str = Field(description="Brief explanation of classification rationale")


class AnalysisResult(BaseModel):
    """법령 분석 결과"""
    problem_core: str = Field(description="One-line summary of the problem's essence")
    relevant_legal_provisions: List[str] = Field(description="List of relevant legal provisions and summary of their contents related to the problem")
    solution_points: List[str] = Field(description="List of important points to consider for solving this problem")


class GraphState(TypedDict):
    """ParentGraph 상태"""
    thread_id: Annotated[str, "개별 입력에 대한 id"]
    user_question: Annotated[str, "사용자의 질문"]
    user_options: Annotated[List[str], "질문과 함께 첨부된 선택지"]
    question_validation: Annotated[Optional[InputValidationResult], "질문과 선택지의 유효성 검사 결과"]
    problem_classification: Annotated[Optional[ProblemClassificationResult], "문제 분류 결과"]
    context: Annotated[Optional[str], "검색 결과"]
    result: Annotated[Optional[AnalysisResult], "최종 결과"]


class SubGraphState(TypedDict):
    """SubGraph 상태"""
    messages: Annotated[List[BaseMessage], "메시지 리스트"]
    problem_core: Annotated[Optional[str], "문제 핵심"]
    relevant_legal_provisions: Annotated[List[str], "관련 법령"]
    solution_points: Annotated[List[str], "해결 포인트"]


# ==================== 프롬프트 정의 ====================

INPUT_VALIDATION_SYSTEM_PROMPT = """Your role is to validate #Instruction# and #Answer Choices# based on the #Judgment Criteria#.
You will get the #Instruction# and #Answer Choices# from the user.
Determine whether the question is valid(is_valid with 1), or not suitable(is_valid with 0) based on the #Judgment Criteria#.
Provide a reason only when the question is invalid.
You don't need to give any explanation when the question is valid.

#Judgment Criteria#
- Ignore typographical errors.
- DO NOT CARE about logic flaws, inaccuracies in the #Answer Choices# and the #Instruction#.
- Confirm that the #Instruction# format follows standard multiple-choice question conventions.
- The #Answer Choices# have to be specific statements or descriptions, NOT just symbols like ○×○○, ○○××, etc.
- If the #Instruction# asks about evaluating multiple statements, the question MUST provide the actual statements to be evaluated.
- Questions that only provide symbol combinations without the corresponding statements are INVALID.
- If the #Instruction# refers to explanations or statements but doesn't provide the actual content to evaluate, the question is INVALID.
"""

PROBLEM_CLASSIFICATION_SYSTEM_PROMPT = """You are an expert in classifying Korean criminal law problems (criminal law, criminal procedure law, correctional law, etc.).
Analyze the given problem and classify it into all applicable types using multi-label classification.
Each problem has Question and Answer Choices.

#Problem Type Definitions#

1. 법령규정형(Statutory Regulation Type): Problems directly asking about the text, requirements, effects, or procedures of specific statutory provisions
   - 예: "○○죄에 대한 설명으로 옳은 것은?", "○○법 제○조에 규정된..."
   - Cases asking about the content of the statute itself rather than interpretation or application

2. 판례적용형(Case Law Application Type): Problems presenting specific factual situations and requiring inference of Supreme Court case law application and conclusions
   - 예: "甲이 乙과 부부싸움을 하다가...", "의사 甲이 환자 A에게..."
   - Structure: factual situation → legal principle application → conclusion derivation

3. 제도용어정의형(Institutional Terminology Definition Type): Problems asking about definitions of theories, institutions, or terminology in criminology, criminal policy, probation, etc.
   - 예: "회복적 사법에 대한 설명", "다이버전 프로그램에 대한 설명"
   - Theoretical concepts or policy institutional meanings and characteristics

4. 절차법규정형(Procedural Law Regulation Type): Problems asking about procedural regulations and principles of criminal procedure law
   - 예: "상소에 대한 설명", "증거능력에 대한 설명", "공판절차에 대한 설명"
   - Legal regulations related to criminal procedure progress

5. 교정보호관찰규정형(Correctional Probation Regulation Type): Problems asking about specific regulations of correctional laws and probation-related laws
   - 예: "형의 집행 및 수용자의 처우에 관한 법률상...", "보호관찰 등에 관한 법률상..."
   - Detailed regulations on correctional facility operations, prisoner treatment, probation-related matters

6. 실체법이론형(Substantive Law Theory Type): Problems asking about theoretical concepts and principles of criminal law
   - 예: "착오에 대한 설명", "공동정범에 대한 설명", "부작위범에 대한 설명"
   - Problems requiring systematic understanding of criminal law theory

#Classification Rules#
- One problem can belong to multiple types, so select all applicable types
- If a problem presents factual situations while requiring statutory interpretation, select both "case_law_application_type" and "statutory_regulation_type"
- If a problem cites specific provisions while asking about theoretical background, select both "statutory_regulation_type" and "substantive_law_theory_type"
- Problems related to corrections or probation can simultaneously have "correctional_probation_regulation_type" and other types depending on content

Use Korean type names (법령규정형, 판례적용형, etc.) in your response.
"""

RAG_AGENT_SYSTEM_PROMPT = """You are an AI agent that analyzes Korean criminal law problems and finds relevant legal provisions.

## Your Tasks:
1. Read and understand the user's problem
2. Find relevant legal provisions
3. Organize and present the findings

## Available Tools:
- **search_article_by_id**: Find specific legal articles by article number (e.g., "형법 제12조")
- **retrieve**: Search for relevant legal provisions using keywords. The filter parameter has to be one of the ## Supported Legal Codes

## Supported Legal Codes:
형법, 형사소송법, 폭력행위등처벌에관한법률, 부정수표단속법, 도로교통법, 특정범죄가중처벌등에관한법률, 마약류불법거래방지에관한특례법, 소송촉진등에관한특례법, 벌금미납자의사회봉사집행에관한특례법

## Work Process:
1. Identify key keywords from the problem
2. Use retrieve tool to search for relevant legal provisions
3. Use search_article_by_id tool for specific articles when needed
4. Organize results in the format below

## Response Format:
**Problem Core:**
- (One-line summary of the problem's essence)

**Relevant Legal Provisions:**
- Article Number: (Content summary)

**Solution Points:**
- (Important points to consider for solving this problem)

## Important Rules:
- Always use tools to verify accurate legal content
- Don't speculate - only use information found through tools
- Write article numbers accurately (e.g., "형법 제12조", "형사소송법 제109조의2")
- If there is no appropriate option with can solve the problem, Rethink or retrieve more information.
- In the Solution Points, provide the relevant legal provisions and solution points"""

FALLBACK_SYSTEM_PROMPT = """You are an AI agent that analyzes Korean criminal law problems and finds relevant legal provisions.

## Your Tasks:
1. Read and understand the history of the conversation from the user.
2. Find relevant legal provisions about the human's problem.
3. Organize and present the findings in the format below.

## Response Format:
**Problem Core:**
- (One-line summary of the problem's essence)

**Relevant Legal Provisions:**
- Article Number: (Content summary)
- Article Number: (Content summary)

**Solution Points:**
- (Important points to consider for solving this problem)

## Important Rules:
- Don't speculate - Firstly, Utilize the information in the history of the conversation.
- If you don't have enough information, Utilize general criminal law knowledge."""

FALLBACK_USER_PROMPT = """# History
{history_text}
"""


# ==================== 체인 생성 함수들 ====================

def make_validation_chain():
    """유효성 검사 체인 생성"""
    validator = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        temperature=0,
    ).with_structured_output(InputValidationResult)

    validation_prompt = ChatPromptTemplate([
        ("system", INPUT_VALIDATION_SYSTEM_PROMPT),
        ("user", "#Instruction#\n{instruction}\n\n#Answer Choices#\n{choices}")
    ])

    return validation_prompt | validator


def make_classification_chain():
    """문제 분류 체인 생성"""
    classifier = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        temperature=0,
    ).with_structured_output(ProblemClassificationResult)

    classification_prompt = ChatPromptTemplate([
        ("system", PROBLEM_CLASSIFICATION_SYSTEM_PROMPT),
        ("user", "#Problem#\nQuestion:\n{question}\n\nAnswer Choices:\n{choices}\n\nAnalyze the above problem and classify it into all applicable types, providing reasoning for your classification.")
    ])

    return classification_prompt | classifier


def make_fallback_handling_chain():
    """Fallback 처리 체인 생성"""
    fallback_handler = init_chat_model(
        model="gpt-4o-mini",
        model_provider="openai",
        temperature=0,
    ).with_structured_output(AnalysisResult)

    fallback_prompt = ChatPromptTemplate([
        ("system", FALLBACK_SYSTEM_PROMPT),
        ("user", FALLBACK_USER_PROMPT),
    ])

    return fallback_prompt | fallback_handler


# ==================== ParentGraph 노드 함수들 ====================

def validate_question(state: GraphState) -> GraphState:
    """질문과 선택지 유효성 검사"""
    logger.info("=== 질문 유효성 검사 시작 ===")
    
    question = state['user_question']
    options = state['user_options']
    choices = "\n".join([f"{choice}. {option}" for option, choice in zip(options, ['A', 'B', 'C', 'D'])])
    
    validation_chain = make_validation_chain()
    result = validation_chain.invoke({"instruction": question, "choices": choices})
    
    logger.info(f"유효성 검사 결과: {result.is_valid}")
    return {"question_validation": result}


def classify_problem(state: GraphState) -> GraphState:
    """문제 분류"""
    logger.info("=== 문제 분류 시작 ===")
    
    question = state['user_question']
    options = state['user_options']
    choices = "\n".join([f"{choice}. {option}" for option, choice in zip(options, ['A', 'B', 'C', 'D'])])
    
    classification_chain = make_classification_chain()
    result = classification_chain.invoke({"question": question, "choices": choices})
    
    logger.info(f"분류 결과: {result.classifications}")
    return {"problem_classification": result}


def handle_failure(state: GraphState) -> GraphState:
    """실패 케이스 처리"""
    logger.info("=== 실패 케이스 처리 ===")
    validation_result = state.get('question_validation')
    reason = validation_result.reason if validation_result else "Unknown error"
    logger.warning(f"처리 실패: {reason}")
    return {"result": None}


def call_rag_agent(state: GraphState) -> GraphState:
    """RAG 에이전트 호출 (SubGraph)"""
    logger.info("=== RAG 에이전트 호출 시작 ===")
    
    question = state['user_question']
    options = state['user_options']
    choices = "\n".join([f"{choice}. {option}" for option, choice in zip(options, ['A', 'B', 'C', 'D'])])
    input_message = f"Question: {question}\n\nOptions: \n{choices}"
    
    # SubGraph 인스턴스를 try 블록 밖에서 생성 (메모리 공유를 위해)
    subgraph = create_rag_subgraph()
    config = {"configurable": {"thread_id": state['thread_id']}, "recursion_limit": 25}
    
    try:
        # 정상적인 SubGraph 실행
        result = subgraph.invoke(
            {"messages": [HumanMessage(content=input_message)]},
            config=config
        )
        
        # 결과 추출
        if result and result.get('messages'):
            last_message = result['messages'][-1]
            if hasattr(last_message, 'content') and hasattr(last_message.content, 'problem_core'):
                # 구조화된 응답인 경우
                content = last_message.content
                analysis_result = AnalysisResult(
                    problem_core=content.problem_core,
                    relevant_legal_provisions=content.relevant_legal_provisions,
                    solution_points=content.solution_points
                )
            else:
                # 텍스트 응답인 경우 기본값 설정
                analysis_result = AnalysisResult(
                    problem_core="문제 분석 완료",
                    relevant_legal_provisions=["관련 법령 검색 완료"],
                    solution_points=["해결 방안 제시"]
                )
        else:
            analysis_result = None
            
        logger.info("RAG 에이전트 호출 완료")
        return {"result": analysis_result}
        
    except GraphRecursionError as e:
        logger.warning(f"Recursion limit 초과 감지: {e}")
        logger.info("대화 내역을 바탕으로 강제 답변을 생성합니다.")
        
        # Memory에서 대화 내역 가져오기 (같은 subgraph 인스턴스 사용)
        try:
            thread_state = subgraph.get_state({"configurable": {"thread_id": state['thread_id']}})
            
            if thread_state and 'messages' in thread_state.values:
                conversation_history = thread_state.values['messages']
                
                # 대화 내역을 문자열로 변환
                history_text = "\n".join([
                    f"{msg.type}: {msg.content}" 
                    for msg in conversation_history 
                    if hasattr(msg, 'type') and hasattr(msg, 'content')
                ])
                
                logger.info(f"대화 내역 추출 완료: {len(conversation_history)}개 메시지")
                
                # 간단한 LLM 호출로 답변 생성
                fallback_handling_chain = make_fallback_handling_chain()
                analysis_result = fallback_handling_chain.invoke({"history_text": history_text})
                
                logger.info("Fallback 처리로 답변 생성 완료")
                return {"result": analysis_result}
            else:
                logger.warning("대화 내역을 찾을 수 없음")
                analysis_result = None
                
        except Exception as memory_error:
            logger.error(f"Memory 조회 실패: {memory_error}")
            analysis_result = None
        
        return {"result": analysis_result}
        
    except Exception as e:
        logger.error(f"RAG 에이전트 호출 실패: {e}")
        return {"result": None}


# ==================== SubGraph 노드 함수들 ====================

def rag_agent_node(state: SubGraphState) -> SubGraphState:
    """RAG 에이전트 노드"""
    logger.info("--- RAG 에이전트 노드 실행 ---")
    
    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # RAG 도구 가져오기
    tools = get_rag_tools()
    
    # ReAct 에이전트 생성
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=RAG_AGENT_SYSTEM_PROMPT,
        response_format=AnalysisResult,
    )
    
    # 에이전트 실행
    messages = state["messages"]
    result = agent.invoke({"messages": messages})
    
    return {"messages": result["messages"]}


# ==================== 조건부 라우팅 ====================

def validity_checker(state: GraphState) -> Literal["PASS", "FAIL"]:
    """유효성 검사 결과에 따른 라우팅"""
    question_validation = state['question_validation']
    if question_validation and question_validation.is_valid == 1:
        return "PASS"
    else:
        return "FAIL"


# ==================== 그래프 생성 함수들 ====================

def create_rag_subgraph():
    """RAG SubGraph 생성"""
    logger.info("RAG SubGraph 생성 중...")
    
    # 메모리 초기화
    memory = MemorySaver()
    
    # SubGraph 구성
    subgraph = StateGraph(SubGraphState)
    subgraph.add_node("rag_agent", rag_agent_node)
    subgraph.add_edge(START, "rag_agent")
    subgraph.add_edge("rag_agent", END)
    
    # 컴파일
    compiled_subgraph = subgraph.compile(checkpointer=memory)
    logger.info("RAG SubGraph 생성 완료")
    
    return compiled_subgraph


def create_parent_graph():
    """ParentGraph 생성"""
    logger.info("ParentGraph 생성 중...")
    
    # ParentGraph 구성
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("validate_question", validate_question)
    workflow.add_node("handle_failure", handle_failure)
    workflow.add_node("classify_problem", classify_problem)
    workflow.add_node("call_rag_agent", call_rag_agent)
    
    # 엣지 추가
    workflow.add_edge(START, "validate_question")
    
    # 조건부 엣지
    workflow.add_conditional_edges(
        "validate_question",
        validity_checker,
        {
            "PASS": "classify_problem",
            "FAIL": "handle_failure",
        },
    )
    
    workflow.add_edge("classify_problem", "call_rag_agent")
    workflow.add_edge("call_rag_agent", END)
    workflow.add_edge("handle_failure", END)
    
    # 컴파일
    compiled_graph = workflow.compile()
    logger.info("ParentGraph 생성 완료")
    
    return compiled_graph


# ==================== 메인 함수 ====================

def main():
    """테스트용 메인 함수"""
    print("=== 법령 분석 통합 워크플로우 테스트 ===")
    
    # ParentGraph 생성
    graph = create_parent_graph()
    
    # 테스트 입력
    test_input = {
        "thread_id": "test_001",
        "user_question": "A가 B를 살해한 후 시체를 유기했다. 이 경우 A에게 적용될 수 있는 죄명은?",
        "user_options": [
            "살인죄와 시체유기죄",
            "살인죄만 적용",
            "시체유기죄만 적용",
            "살인죄와 시체손괴죄"
        ]
    }
    
    # 실행
    result = graph.invoke(test_input)
    
    print("\n=== 실행 결과 ===")
    print(f"스레드 ID: {result.get('thread_id')}")
    print(f"유효성 검사: {result.get('question_validation')}")
    print(f"문제 분류: {result.get('problem_classification')}")
    print(f"최종 결과: {result.get('result')}")


if __name__ == "__main__":
    main() 