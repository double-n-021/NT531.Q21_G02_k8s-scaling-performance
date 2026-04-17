#!/bin/bash
# scripts/run_kb2_suite.sh
# ============================================================
# NT531 Automated Suite — Kịch bản 2: Reactive Scaling (HPA)
# ============================================================
# Tự động chạy trọn bộ 5 profiles cho chiến lược HPA.
# ============================================================

STRATEGY="reactive-hpa"
CONFIG="config/hpa_scenario.yaml"
HOST=${1:-"http://100.99.156.17:8888"}
REPEATS=${2:-3}

PROFILES=("stable" "ramp" "spike" "spike_recovery" "oscillating")

echo "============================================================"
echo "  NT531 MASTER SUITE: STRATEGY $STRATEGY"
echo "  Target Host: $HOST"
echo "  Config:      $CONFIG"
echo "  Executing all ${#PROFILES[@]} profiles, each with $REPEATS repeats..."
echo "============================================================"

# Đảm bảo thư mục results tồn tại
mkdir -p results

for P in "${PROFILES[@]}"; do
    echo -e "\n>>> STARTING PROFILE: $P <<<"
    
    # Gán các biến môi trường
    export LOCUST_CONFIG="$CONFIG"
    export LOCUST_OUT_DIR=${LOCUST_OUT_DIR:-"results"}
    
    # Lấy reset_wait từ config (mặc định 180 nếu không thấy)
    WAIT_TIME=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c['experiment'].get('reset_wait', 180))")
    
    bash "./scripts/run_benchmark.sh" "$STRATEGY" "$P" "$REPEATS" "$HOST" "$WAIT_TIME"
    
    echo -e "\e[32m>>> FINISHED PROFILE: $P <<<\e[0m"
    echo "------------------------------------------------------------"
done

echo "============================================================"
echo "  SUITE COMPLETED: $STRATEGY"
echo "  Data saved to results/${STRATEGY}_*"
echo "============================================================"
