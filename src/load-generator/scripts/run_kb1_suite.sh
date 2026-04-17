#!/bin/bash
# scripts/run_kb1_suite.sh
# ============================================================
# NT531 Master Suite — LINUX VERSION (Dùng cho VPS)
# Chạy trọn bộ 5 Profiles cho Static Baseline
# ============================================================
# Usage:
#   ./scripts/run_kb1_suite.sh <K> <host> [repeats]
# Example:
#   ./scripts/run_kb1_suite.sh 2 http://192.168.1.100:8000 5
# ============================================================

set +e

K=${1:?"Usage: $0 <K> <host> [repeats]"}
HOST=${2:?"Usage: $0 <K> <host> [repeats]"}
REPEATS=${3:-5}

CONFIG="config/k${K}.yaml"
STRATEGY="static-k${K}"
PROFILES=("stable" "ramp" "spike" "spike_recovery" "oscillating")

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ ! -f "$CONFIG" ]; then
    echo "ERROR: Không tìm thấy file config $CONFIG. Đảm bảo bạn chạy từ thư mục src/load-generator/"
    exit 1
fi

echo -e "\e[36m============================================================\e[0m"
echo -e "\e[36m  NT531 MASTER SUITE: STRATEGY $STRATEGY \e[0m"
echo "  Target Host: $HOST"
echo "  Config:      $CONFIG"
echo "  Executing all 5 profiles, each with $REPEATS repeats..."
echo -e "\e[36m============================================================\e[0m"

for P in "${PROFILES[@]}"; do
    echo ""
    echo -e "\e[33m>>> STARTING PROFILE: $P <<<\e[0m"
    
    # Gán các biến môi trường
    export LOCUST_CONFIG="$CONFIG"
    export LOCUST_OUT_DIR="../../data/kb1_static/k${K_LEVEL}"
    
    # Lấy reset_wait từ config (mặc định 420 nếu không thấy)
    WAIT_TIME=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c['experiment'].get('reset_wait', 420))")
    
    bash "./scripts/run_benchmark.sh" "$STRATEGY" "$P" "$REPEATS" "$HOST" "$WAIT_TIME"
    
    echo -e "\e[32m>>> FINISHED PROFILE: $P <<<\e[0m"
    echo "------------------------------------------------------------"
done

echo ""
echo -e "\e[35m[SUCCESS] Hoàn thành trọn bộ kịch bản Static Baseline cho K=$K!\e[0m"
echo "Dữ liệu đã được lưu tại thư mục: $PROJECT_DIR/results/"
