# Law Agent System with KMMLU Evaluation

## 🎯 프로젝트 개요

이 프로젝트는 **한국 형법 전문 AI 에이전트 시스템**을 구축하고, KMMLU(Korean Massive Multitask Language Understanding) 벤치마크의 Criminal-Law 카테고리를 사용하여 성능을 평가하는 시스템입니다.

### 주요 기능
- 🤖 **AI 에이전트 시스템**: GPT-4o-mini 기반 한국 형법 전문 에이전트
- 🔍 **RAG 시스템**: 한국 형법 조문 및 판례 검색 시스템
- 📊 **자동 평가**: KMMLU Criminal-Law 데이터셋을 활용한 자동 평가
- ☁️ **OpenAI Batch API**: 대용량 평가를 위한 배치 처리 시스템
- 🐳 **Docker 환경**: 완전 컨테이너화된 실행 환경

## 🏗️ 시스템 아키텍처

```
Law Agent System
├── 🤖 Agent Core (GPT-4o-mini)
│   ├── Question Validator
│   ├── Problem Classifier  
│   └── RAG Retriever
├── 🔍 RAG System
│   ├── Vector DB (text-embedding-3-small)
│   ├── Legal Document Store
│   └── Semantic Search
├── 📊 Evaluation System
│   ├── KMMLU Dataset Loader
│   ├── Batch File Generator
│   └── OpenAI Batch API Client
└── 🐳 Docker Environment
    ├── Chrome/ChromeDriver
    ├── Python 3.11
    └── Poetry Dependencies
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd law-agent

# 환경 변수 설정
cp .env.example .env
# .env 파일에 OpenAI API 키 설정
echo "OPENAI_API_KEY=your-api-key-here" >> .env
```

### 2. 전체 시스템 실행 (원클릭)

```bash
# Docker 환경에서 전체 시스템 구축 및 평가 실행
cd docker
docker-compose up --build

# 또는 개별 스크립트 실행
docker-compose run law-agent python scripts/create_batch_upload.py
docker-compose run law-agent python scripts/evaluate_batch_results.py
```

### 3. 수동 실행 (단계별)

```bash
# 1단계: 배치 파일 생성 및 업로드
cd docker
docker-compose run law-agent python scripts/create_batch_upload.py

# 2단계: 배치 결과 평가 (배치 완료 후)
docker-compose run law-agent python scripts/evaluate_batch_results.py
```

## 📋 요구사항

### 시스템 요구사항
- Docker & Docker Compose
- 최소 4GB RAM
- 인터넷 연결 (API 호출 및 데이터 다운로드)

### API 요구사항
- OpenAI API 키
- GPT-4o-mini 액세스 권한
- text-embedding-3-small 액세스 권한

## 🔧 기술 스택

### 핵심 기술
- **Language Model**: GPT-4o-mini
- **Embedding Model**: text-embedding-3-small  
- **Vector Database**: FAISS
- **Web Framework**: LangGraph
- **Dependency Manager**: Poetry
- **Containerization**: Docker + Docker Compose

### 주요 라이브러리
```toml
[tool.poetry.dependencies]
python = "^3.11"
langchain = "^0.3.1"
langgraph = "^0.2.28"
openai = "^1.51.0"
datasets = "^3.0.1"
faiss-cpu = "^1.8.0"
beautifulsoup4 = "^4.12.3"
selenium = "^4.25.0"
```

## 📊 성능 벤치마크

### KMMLU Criminal-Law 평가 결과

| 메트릭 | 값 |
|--------|-----|
| **총 문제 수** | 200개 |
| **정답 수** | 1개 |
| **오답 수** | 4개 |
| **실패 수** | 195개 |
| **정확도** | 0.50% |

### 배치 처리 성능

| 메트릭 | 값 |
|--------|-----|
| **배치 ID** | `batch_686a8d96f8088190ace4e47923a1d83f` |
| **처리 시간** | ~10분 (OpenAI 배치 처리) |
| **Parent Graph 평가** | ~22초 (5개 문제) |
| **배치 파일 크기** | ~15KB |

## 📁 프로젝트 구조

```
law-agent/
├── 📄 README.md                    # 프로젝트 문서
├── 📄 pyproject.toml               # Poetry 의존성 관리
├── 📄 .env.example                 # 환경 변수 템플릿
├── 📁 src/                         # 소스 코드
│   ├── 📁 agent/                   # 에이전트 시스템
│   │   ├── workflow.py             # 메인 워크플로우
│   │   └── rag_retriever.py        # RAG 검색 시스템
│   ├── 📁 evaluation/              # 평가 시스템
│   │   └── kmmlu_evaluator.py      # KMMLU 평가기
│   ├── 📁 data_collector/          # 데이터 수집
│   │   └── web_scraper.py          # 웹 크롤링
│   └── 📁 vector_db/               # 벡터 데이터베이스
│       └── embeddings.py           # 임베딩 관리
├── 📁 scripts/                     # 실행 스크립트
│   ├── create_batch_upload.py      # 배치 생성 및 업로드
│   ├── evaluate_batch_results.py   # 배치 결과 평가
│   └── process_documents_and_embed.py # 문서 처리 및 임베딩
├── 📁 docker/                      # Docker 환경
│   ├── Dockerfile                  # 컨테이너 이미지
│   ├── docker-compose.yml          # 컨테이너 오케스트레이션
│   └── .dockerignore               # Docker 제외 파일
├── 📁 data/                        # 데이터 저장소
│   ├── 📁 batch/                   # 배치 API 파일
│   │   ├── input_batch.jsonl       # 배치 입력 파일 ✅
│   │   ├── output_batch.jsonl      # 배치 출력 파일 ✅
│   │   ├── input_id.txt            # 입력 배치 ID
│   │   └── output_id.txt           # 출력 배치 ID
│   ├── 📁 embeddings/              # 벡터 임베딩
│   └── 📁 documents/               # 원본 문서
└── 📁 tests/                       # 테스트 코드
```

## 🔄 워크플로우

### 1. 데이터 수집 및 전처리
```bash
# 한국 형법 조문 및 판례 데이터 수집
python scripts/process_documents_and_embed.py
```

### 2. 벡터 데이터베이스 구축
- 📚 **원본 데이터**: 한국 형법 조문, 판례 문서
- 🔄 **전처리**: 문서 분할, 정제, 구조화
- 🎯 **임베딩**: text-embedding-3-small로 벡터화
- 💾 **저장**: FAISS 벡터 데이터베이스 생성

### 3. 에이전트 시스템 구축
- 🔍 **질문 유효성 검사**: 법률 질문 적합성 판단
- 🏷️ **문제 분류**: 법률 문제 유형 분류
- 🔎 **RAG 검색**: 관련 조문 및 판례 검색
- 🤖 **답변 생성**: GPT-4o-mini 기반 답변 생성

### 4. KMMLU 평가 실행
```bash
# 전체 평가 워크플로우
python scripts/create_batch_upload.py      # 배치 업로드
python scripts/evaluate_batch_results.py   # 결과 평가
```

## 🎯 주요 스크립트

### 1. `scripts/create_batch_upload.py`
- **기능**: KMMLU 데이터셋 처리 및 OpenAI 배치 업로드
- **프로세스**:
  1. KMMLU Criminal-Law 데이터셋 로드
  2. Parent Graph로 평가 실행
  3. 배치 파일 생성 (`input_batch.jsonl`)
  4. OpenAI Batch API 업로드
  5. 배치 ID 저장 (`input_id.txt`)

### 2. `scripts/evaluate_batch_results.py`
- **기능**: 배치 결과 모니터링 및 최종 평가
- **프로세스**:
  1. 배치 ID 확인 (`input_id.txt`)
  2. 배치 상태 모니터링 (최대 10분)
  3. 완료시 결과 다운로드 (`output_batch.jsonl`)
  4. 출력 배치 ID 저장 (`output_id.txt`)
  5. 최종 평가 실행 및 결과 출력

## 🐳 Docker 설정

### Dockerfile 구성
```dockerfile
FROM python:3.11-slim

# Chrome 및 ChromeDriver 설치
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') && \
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/

# Poetry 설치 및 의존성 관리
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev
```

### Docker Compose 구성
```yaml
version: '3.8'

services:
  law-agent:
    build:
      context: ../
      dockerfile: docker/Dockerfile
    container_name: law-agent
    volumes:
      - ../src:/app/src
      - ../data:/app/data
      - ../scripts:/app/scripts
      - ../.env:/app/.env
    environment:
      - PYTHONPATH=/app
    command: >
      bash -c "
        echo '🚀 Law Agent 통합 워크플로우 테스트 시작...' &&
        python scripts/create_batch_upload.py &&
        python scripts/evaluate_batch_results.py
      "
```

## 📊 제출 파일

### 필수 제출 파일 ✅
- **배치 입력 파일**: `data/batch/input_batch.jsonl`
- **배치 출력 파일**: `data/batch/output_batch.jsonl`
- **벤치마크 점수**: README에 포함됨
- **전체 소스 코드**: 2GB 이내

### 배치 API 파일 구조
```json
// input_batch.jsonl 예시
{
  "custom_id": "q001",
  "method": "POST",
  "url": "/v1/responses",
  "body": {
    "model": "gpt-4o-mini",
    "instructions": "You are an expert in Korean criminal law...",
    "input": "Question: ... Context: ...",
    "temperature": 0
  }
}

// output_batch.jsonl 예시
{
  "id": "batch_req_xxx",
  "custom_id": "q001",
  "response": {
    "status_code": 200,
    "body": {
      "output": [{"content": [{"text": "A"}]}]
    }
  }
}
```

## 🚀 실행 시간

### 전체 실행 시간 (배치 API 제외)
- **데이터 수집**: ~5분
- **벡터 DB 구축**: ~10분
- **에이전트 시스템 구축**: ~2분
- **배치 파일 생성**: ~30초
- **결과 평가**: ~10초
- **총 소요 시간**: ~18분 (1시간 이내) ✅

### 배치 API 처리 시간
- **OpenAI 배치 처리**: ~10분 (외부 API 응답 시간)

## 🔧 커스터마이징

### 환경 변수 설정
```bash
# .env 파일 설정
OPENAI_API_KEY=your-api-key-here
BATCH_SIZE=5
SLEEP_TIME=5
MAX_WAIT_TIME=600
```

### 배치 크기 조정
```python
# scripts/create_batch_upload.py
evaluator = KMMLUEvaluator(batch_size=5, sleep_time=5)
```

## 🐛 문제 해결

### 일반적인 문제
1. **Docker 빌드 실패**
   ```bash
   docker-compose up --build --force-recreate
   ```

2. **API 키 오류**
   ```bash
   # .env 파일 확인
   cat .env | grep OPENAI_API_KEY
   ```

3. **배치 상태 확인**
   ```bash
   docker-compose run law-agent python -c "
   from src.evaluation.kmmlu_evaluator import KMMLUEvaluator
   evaluator = KMMLUEvaluator()
   with open('data/batch/input_id.txt', 'r') as f:
       batch_id = f.read().strip()
   print(f'Batch Status: {evaluator.monitor_batch(batch_id)}')
   "
   ```

### 로그 확인
```bash
# 컨테이너 로그 확인
docker-compose logs law-agent

# 실시간 로그 모니터링
docker-compose logs -f law-agent
```

## 📚 추가 자료

### 관련 논문 및 자료
- [KMMLU 논문](https://arxiv.org/abs/2402.11548)
- [OpenAI Batch API 문서](https://platform.openai.com/docs/guides/batch)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)

### 개발 참고사항
- 모든 코드는 Python 3.11 환경에서 테스트됨
- Poetry를 사용한 의존성 관리
- Docker 환경에서의 완전 자동화 실행
- OpenAI API 비용 최적화를 위한 배치 처리

---

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

**© 2024 Law Agent System. All rights reserved.**