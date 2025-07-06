#!/bin/bash

# KMMLU 배치 파일 생성 및 업로드 스크립트
# create_batch_upload.py만 실행하여 OpenAI Batch API에 업로드

# 스크립트가 위치한 디렉터리로 이동
cd "$(dirname "$0")"

# scripts 디렉터리 경로 (상위 디렉터리)
SCRIPTS_DIR="../"

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo -e "${BLUE}KMMLU 배치 파일 생성 및 업로드${NC}"
echo "=========================================="

# scripts 디렉터리 존재 확인
if [ ! -d "$SCRIPTS_DIR" ]; then
    echo -e "${RED}오류: scripts 디렉터리를 찾을 수 없습니다.${NC}"
    exit 1
fi

# 실행할 스크립트
script="create_batch_upload.py"
script_path="$SCRIPTS_DIR/$script"

# 파일 존재 확인
if [ ! -f "$script_path" ]; then
    echo -e "${RED}오류: $script_path 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

# 필요한 데이터 디렉터리 확인
if [ ! -d "../../data/embeddings" ]; then
    echo -e "${RED}오류: data/embeddings 디렉터리가 없습니다.${NC}"
    echo -e "${YELLOW}먼저 process_documents_and_embed.py를 실행하여 벡터DB를 생성하세요.${NC}"
    exit 1
fi

echo -e "${YELLOW}실행 중: KMMLU 배치 파일 생성 및 업로드${NC}"
echo "📊 전체 200개 문제 처리 예상"
echo "⏰ 예상 소요 시간: 약 20분"
echo "------------------------------------------"

# Python 스크립트 실행
python3 "$script_path"

# 실행 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 배치 파일 생성 및 업로드 완료${NC}"
    echo ""
    echo "📁 생성된 파일들:"
    echo "  - data/batch/input_batch.jsonl"
    echo "  - data/batch/input_id.txt"
    echo ""
    echo -e "${BLUE}다음 단계: eval_result.sh를 실행하여 결과를 확인하세요${NC}"
else
    echo -e "${RED}✗ 배치 파일 생성 및 업로드 실패${NC}"
    exit 1
fi

echo "=========================================="
echo -e "${GREEN}배치 업로드 완료!${NC}"
echo "==========================================" 