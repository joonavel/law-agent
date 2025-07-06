#!/bin/bash

# KMMLU 배치 결과 평가 스크립트
# evaluate_batch_results.py만 실행하여 OpenAI Batch API 결과를 평가

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
echo -e "${BLUE}KMMLU 배치 결과 평가${NC}"
echo "=========================================="

# scripts 디렉터리 존재 확인
if [ ! -d "$SCRIPTS_DIR" ]; then
    echo -e "${RED}오류: scripts 디렉터리를 찾을 수 없습니다.${NC}"
    exit 1
fi

# 실행할 스크립트
script="evaluate_batch_results.py"
script_path="$SCRIPTS_DIR/$script"

# 파일 존재 확인
if [ ! -f "$script_path" ]; then
    echo -e "${RED}오류: $script_path 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

# 필요한 파일들 확인
if [ ! -f "../../data/batch/input_id.txt" ]; then
    echo -e "${RED}오류: data/batch/input_id.txt 파일이 없습니다.${NC}"
    echo -e "${YELLOW}먼저 make_batch.sh를 실행하여 배치를 생성하세요.${NC}"
    exit 1
fi

# 배치 ID 확인 및 표시
batch_id=$(cat ../../data/batch/input_id.txt 2>/dev/null)
if [ -n "$batch_id" ]; then
    echo -e "${BLUE}📋 배치 ID: ${batch_id}${NC}"
else
    echo -e "${RED}오류: 배치 ID를 읽을 수 없습니다.${NC}"
    exit 1
fi

echo -e "${YELLOW}실행 중: 배치 결과 모니터링 및 평가${NC}"
echo "⏳ 배치 완료까지 최대 10분 대기"
echo "📊 완료 후 자동으로 결과 평가 진행"
echo "------------------------------------------"

# Python 스크립트 실행
python3 "$script_path"

# 실행 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 배치 결과 평가 완료${NC}"
    echo ""
    echo "📁 생성된 파일들:"
    if [ -f "../../data/batch/output_batch.jsonl" ]; then
        echo "  - data/batch/output_batch.jsonl"
    fi
    if [ -f "../../data/batch/output_id.txt" ]; then
        echo "  - data/batch/output_id.txt"
    fi
    echo ""
    echo -e "${BLUE}평가 결과는 위 로그에서 확인하세요${NC}"
else
    echo -e "${RED}✗ 배치 결과 평가 실패${NC}"
    echo ""
    echo -e "${YELLOW}배치가 아직 완료되지 않았을 수 있습니다.${NC}"
    echo -e "${YELLOW}잠시 후 다시 시도해보세요.${NC}"
    exit 1
fi

echo "=========================================="
echo -e "${GREEN}평가 완료!${NC}"
echo "==========================================" 