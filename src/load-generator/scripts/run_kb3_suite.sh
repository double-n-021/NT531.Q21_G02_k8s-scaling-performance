#!/bin/bash
# scripts/run_kb3_suite.sh
# ============================================================
# NT531 Automated Suite — Kịch bản 3: Proactive Scaling (KEDA)
# ============================================================

STRATEGY="proactive-keda"
CONFIG="config/proactive_scenario.yaml"
HOST=${1:-"http://100.99.156.17:8888"}
REPEATS=${2:-3}

PROFILES=("ramp" "spike_recovery")

mkdir -p results

for P in "${PROFILES[@]}"; do
    echo -e "\n>>> STARTING PROACTIVE PROFILE: $P <<<"
    export LOCUST_CONFIG="$CONFIG"
    export LOCUST_OUT_DIR=${LOCUST_OUT_DIR:-"../../data/kb3_proactive"}
    
    # Lấy reset_wait từ config
    WAIT_TIME=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFIG')); print(c['experiment'].get('reset_wait', 180))")
    
    bash "./scripts/run_benchmark.sh" "$STRATEGY" "$P" "$REPEATS" "$HOST" "$WAIT_TIME"
    
    echo -e "\e[32m>>> FINISHED PROFILE: $P <<<\e[0m"
    echo "------------------------------------------------------------"
done
