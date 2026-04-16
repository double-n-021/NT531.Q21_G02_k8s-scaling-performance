#!/bin/bash
# scripts/run_benchmark.sh
# ============================================================
# NT531 Benchmark Automation — Chạy N runs cho 1 tổ hợp (strategy × profile)
# ============================================================
# Usage:
#   ./scripts/run_benchmark.sh <strategy> <profile> [runs] [host]
#
# Examples:
#   ./scripts/run_benchmark.sh static_k2 spike 5 http://192.168.1.100
#   ./scripts/run_benchmark.sh hpa stable 5 http://192.168.1.100
#   ./scripts/run_benchmark.sh proactive ramp 5 http://192.168.1.100
#
# Output:
#   results/<strategy>_<profile>_run<N>_stats.csv
#   results/<strategy>_<profile>_run<N>_stats_history.csv
#   results/<strategy>_<profile>_run<N>_meta.json
# ============================================================

set -e

STRATEGY=${1:?"Usage: $0 <strategy> <profile> [runs] [host]"}
PROFILE=${2:?"Usage: $0 <strategy> <profile> [runs] [host]"}
RUNS=${3:-5}
HOST=${4:-"http://192.168.1.100"}
RESET_WAIT=${5:-420}  # 7 phút (420 giây)
CONFIG=${LOCUST_CONFIG:-"config/default.yaml"}
OUT_DIR=${LOCUST_OUT_DIR:-"results"}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "============================================================"
echo "  NT531 BENCHMARK"
echo "  Strategy:  ${STRATEGY}"
echo "  Profile:   ${PROFILE}"
echo "  Runs:      ${RUNS}"
echo "  Host:      ${HOST}"
echo "  Config:    ${CONFIG}"
echo "  Reset:     ${RESET_WAIT}s"
echo "============================================================"

cd "$PROJECT_DIR"

for i in $(seq 1 "$RUNS"); do
    RUN_ID="${STRATEGY}_${PROFILE}_run${i}"
    SEED=$((42 + i))  # Seed khác nhau mỗi run nhưng reproducible

    echo ""
    echo "--- Run ${i}/${RUNS}: ${RUN_ID} (seed=${SEED}) ---"
    echo "    Time: $(date '+%Y-%m-%d %H:%M:%S')"

    # 1. Check cluster đã reset sạch
    if [ -f "$SCRIPT_DIR/check_reset.sh" ]; then
        echo "    [CHECK] Verifying cluster reset..."
        bash "$SCRIPT_DIR/check_reset.sh" "$HOST" || {
            echo "    [FAIL] Cluster reset check failed. Aborting."
            exit 1
        }
    fi

    # 2. Chạy Locust
    echo "    [RUN] Starting Locust..."

    if [ "$PROFILE" = "stable" ]; then
        # Stable: dùng --users/--spawn-rate (không dùng LoadShape)
        USERS=$(python3 -c "import yaml; c=yaml.safe_load(open('${CONFIG}')); print(c['profiles']['stable']['users'])")
        DURATION=$(python3 -c "import yaml; c=yaml.safe_load(open('${CONFIG}')); print(c['profiles']['stable']['duration'])")

        PROFILE="$PROFILE" \
        LOCUST_CONFIG="$CONFIG" \
        LOCUST_SEED="$SEED" \
        RUN_ID="$RUN_ID" \
        locust -f locustfile.py \
            --host "$HOST" \
            --headless \
            --users "$USERS" \
            --spawn-rate "$USERS" \
            --run-time "${DURATION}s" \
            --csv "${OUT_DIR}/${RUN_ID}" \
            --csv-full-history
    else
        # Ramp/Spike/Spike-Recovery/Oscillating: dùng LoadShape
        PROFILE="$PROFILE" \
        LOCUST_CONFIG="$CONFIG" \
        LOCUST_SEED="$SEED" \
        RUN_ID="$RUN_ID" \
        locust -f locustfile.py \
            --host "$HOST" \
            --headless \
            --csv "${OUT_DIR}/${RUN_ID}" \
            --csv-full-history
    fi

    echo "    [DONE] Run ${i} completed."

    # 3. Wait for reset (trừ run cuối)
    if [ "$i" -lt "$RUNS" ]; then
        echo "    [WAIT] Waiting ${RESET_WAIT}s for cluster reset..."
        sleep "$RESET_WAIT"
    fi
done

echo ""
echo "============================================================"
echo "  ALL ${RUNS} RUNS COMPLETED: ${STRATEGY}/${PROFILE}"
echo "  Results in: results/${STRATEGY}_${PROFILE}_run*"
echo "============================================================"
