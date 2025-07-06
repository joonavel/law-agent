# Law Agent System

법령 정보를 기반으로 한 AI 에이전트 시스템

## 개요

이 프로젝트는 한국의 형법 및 관련 법령 정보를 수집하고, RAG(Retrieval-Augmented Generation)를 활용한 법령 질의응답 에이전트를 구축합니다.

## 주요 기능

1. **웹 스크래핑**: Selenium을 이용한 법령 정보 수집
2. **데이터 파싱**: 수집된 법령 데이터를 조문별로 구조화
3. **벡터 임베딩**: OpenAI embedding을 이용한 FAISS 벡터 DB 구축
4. **통합 Agent 워크플로우**: LangGraph 함수형 패턴 기반 시스템
   - **ParentGraph**: 질문 유효성 검사, 문제 분류, 라우팅
   - **SubGraph**: RAG 기반 법령 분석 및 조항 검색
5. **RAG 시스템**: 법령 정보 기반 질의응답 및 구조화된 분석 결과

## 기술 스택

- **언어**: Python 3.11+
- **의존성 관리**: Poetry
- **웹 스크래핑**: Selenium, BeautifulSoup
- **벡터 DB**: FAISS (7.9MB 인덱스, 1,347개 법령 조항)
- **LLM**: OpenAI GPT-4o-mini
- **Embedding**: OpenAI text-embedding-3-small
- **Agent 프레임워크**: LangGraph (함수형 패턴)
- **구조화 출력**: Pydantic BaseModel
- **컨테이너**: Docker, docker-compose

## 프로젝트 구조

```
law-agent/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── data_collector/     # 웹 스크래핑 및 파싱
│   ├── vector_db/         # 벡터 DB 관리
│   ├── agent/             # 에이전트 워크플로우
│   └── evaluation/        # KMMLU 평가
├── data/
│   ├── raw/              # 원시 데이터
│   ├── processed/        # 처리된 데이터
│   └── embeddings/       # 벡터 DB 파일
├── scripts/              # 실행 스크립트
└── README.md
```

## 워크플로우 아키텍처

### ParentGraph (메인 워크플로우)
```
START → validate_question → classify_problem → call_rag_agent → END
            ↓ (유효성 실패)
        handle_failure → END
```

1. **validate_question**: 질문과 선택지의 유효성 검사
   - 다중 선택 질문 형식 확인
   - 선택지가 구체적 설명인지 확인 (기호만 있는 경우 거부)
   
2. **classify_problem**: 문제 유형 분류
   - 법령규정형, 판례적용형, 실체법이론형 등 6가지 유형
   - 다중 라벨 분류 지원
   
3. **call_rag_agent**: SubGraph 호출하여 법령 분석 수행
   - GraphRecursionError 발생 시 자동 fallback 처리
   - 대화 내역 기반 강제 답변 생성
4. **handle_failure**: 유효성 검사 실패 시 처리

### SubGraph (RAG 분석)
```
START → rag_agent → END
```

- **rag_agent**: ReAct 패턴 기반 법령 분석
  - 도구: `search_article_by_id`, `retrieve`
  - 출력: 구조화된 `AnalysisResult`
  - Recursion limit 초과 시 자동 fallback 처리

### 상태 관리
- **GraphState**: ParentGraph 전체 상태
- **SubGraphState**: SubGraph 내부 상태
- **MemorySaver**: 대화 기록 및 중간 상태 관리

### Fallback 처리
- **GraphRecursionError** 자동 감지 및 처리
- 대화 내역 기반 강제 답변 생성
- 메모리 조회 실패 시 안전한 예외 처리

## 설치 및 실행

### 1. 환경 설정

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에 OpenAI API 키 설정
```

### 2. Docker 빌드

```bash
docker-compose -f docker/docker-compose.yml build
```

### 3. 컨테이너 실행

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 4. 테스트 실행

```bash
# 통합 워크플로우 테스트 (ParentGraph + SubGraph)
docker-compose -f docker/docker-compose.yml exec law-agent python scripts/test_integrated_workflow.py

# 또는 로컬에서 직접 실행
cd law-agent
python scripts/test_integrated_workflow.py
```

## 개발 상태

- [x] Flow 1: 웹 스크래핑 및 파싱 (완료)
- [x] Flow 2: 벡터 DB 구축 (완료)
- [x] Flow 3: 함수형 패턴 기반 통합 Agent 워크플로우 (완료)
  - [x] ParentGraph: 유효성 검사, 문제 분류, 실패 처리
  - [x] SubGraph: RAG 기반 법령 분석 에이전트
  - [x] 함수형 노드 패턴 적용
- [ ] Flow 4: 성능 최적화 및 고도화
- [ ] KMMLU 평가 시스템

## 라이센스

MIT License 