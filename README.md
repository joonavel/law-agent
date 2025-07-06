# Law Agent System

법령 정보를 기반으로 한 AI 에이전트 시스템

## 개요

이 프로젝트는 한국의 형법 및 관련 법령 정보를 수집하고, RAG(Retrieval-Augmented Generation)를 활용한 법령 질의응답 에이전트를 구축합니다.

## 주요 기능

1. **웹 스크래핑**: Selenium을 이용한 법령 정보 수집
2. **데이터 파싱**: 수집된 법령 데이터를 조문별로 구조화
3. **벡터 임베딩**: OpenAI embedding을 이용한 FAISS 벡터 DB 구축
4. **Agent 워크플로우**: LangGraph를 활용한 에이전트 시스템
5. **RAG 시스템**: 법령 정보 기반 질의응답

## 기술 스택

- **언어**: Python 3.11+
- **의존성 관리**: Poetry
- **웹 스크래핑**: Selenium, BeautifulSoup
- **벡터 DB**: FAISS
- **LLM**: OpenAI GPT-4o-mini
- **Embedding**: OpenAI text-embedding-small
- **Agent 프레임워크**: LangGraph
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
# Flow 1 테스트 (웹 스크래핑 및 파싱)
docker-compose -f docker/docker-compose.yml exec law-agent python scripts/test_flow1.py
```

## 개발 상태

- [x] Flow 1: 웹 스크래핑 및 파싱
- [ ] Flow 2: 벡터 DB 구축
- [ ] Flow 3: Agent 워크플로우
- [ ] Flow 4: RAG 시스템
- [ ] KMMLU 평가 시스템

## 라이센스

MIT License 