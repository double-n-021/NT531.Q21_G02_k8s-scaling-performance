#!/bin/bash
# scripts/check_reset.sh
# ============================================================
# Verified Reset Check — Đảm bảo cluster sạch trước run tiếp theo
# ============================================================
# Kiểm tra:
#   1. Health check endpoint trả HTTP 200
#   2. Latency < 100ms (hệ thống rảnh)
#
# Usage: ./scripts/check_reset.sh [host]
# Exit code: 0 = ready, 1 = not ready
# ============================================================

HOST=${1:-"http://192.168.1.100"}
MAX_RETRIES=30
INTERVAL=10  # giây

echo "    Checking: ${HOST}/health"

for i in $(seq 1 $MAX_RETRIES); do
    # Check 1: HTTP 200
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HOST}/health" 2>/dev/null)
    if [ "$HTTP_CODE" != "200" ]; then
        echo "    [WAIT] Health: HTTP ${HTTP_CODE} (retry ${i}/${MAX_RETRIES})"
        sleep $INTERVAL
        continue
    fi

    # Check 2: Latency thấp
    LATENCY=$(curl -s -o /dev/null -w "%{time_total}" "${HOST}/health" 2>/dev/null)
    LATENCY_MS=$(echo "$LATENCY * 1000" | bc 2>/dev/null || echo "999")

    # So sánh — nếu > 100ms thì chưa sạch
    if [ "$(echo "$LATENCY_MS > 100" | bc 2>/dev/null)" = "1" ]; then
        echo "    [WAIT] Latency: ${LATENCY_MS}ms > 100ms (retry ${i}/${MAX_RETRIES})"
        sleep $INTERVAL
        continue
    fi

    echo "    [OK] Cluster ready — HTTP 200, latency ${LATENCY_MS}ms"
    exit 0
done

echo "    [FAIL] Cluster not ready after $((MAX_RETRIES * INTERVAL))s"
exit 1
