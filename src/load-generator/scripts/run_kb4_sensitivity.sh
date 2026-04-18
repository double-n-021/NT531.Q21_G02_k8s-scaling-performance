#!/bin/bash
# scripts/run_kb4_sensitivity.sh
# Usage: ./scripts/run_kb4_sensitivity.sh <threshold_value> [repeats]

STRATEGY="proactive-keda"
CONFIG="config/proactive_scenario.yaml"
HOST=${HOST:-"http://100.99.156.17:8888"}
THRESHOLD=${1:?"Usage: $0 <threshold_value>"}
REPEATS=${2:-2}

# Chỉ chạy Ramp cho phân tích độ nhạy
PROFILES=("ramp")

export LOCUST_CONFIG="$CONFIG"
# Tự động lưu vào thư mục riêng
export LOCUST_OUT_DIR="../../data/kb4_sensitivity/threshold_${THRESHOLD}"
mkdir -p "$LOCUST_OUT_DIR"

for P in "${PROFILES[@]}"; do
    echo -e "\n>>> STARTING SENSITIVITY TEST (THRESHOLD=$THRESHOLD) | PROFILE: $P <<<"
    bash "./scripts/run_benchmark.sh" "$STRATEGY" "$P" "$REPEATS" "$HOST" 360
    echo -e "\e[32m>>> FINISHED SENSITIVITY PROFILE: $P <<<\e[0m"
    echo "------------------------------------------------------------"
done
