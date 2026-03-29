# mock/mock_server.py
# ============================================================
# Mock FastAPI Server — Test Locust profiles KHÔNG cần cluster
# ============================================================
# Mô phỏng behavior của processing service thật:
# - POST /collect: nhận JSON, giả lập CPU processing, trả response
# - GET /health-check: health probe
# - GET /metrics: fake Prometheus metrics (không cần prometheus_client)
#
# Usage:
#   pip install fastapi uvicorn
#   cd Do-an/src/load-generator
#   python -m uvicorn mock.mock_server:app --host 0.0.0.0 --port 8000
#
# Sau đó test Locust:
#   PROFILE=spike locust -f locustfile.py --host http://localhost:8000 \
#     --headless --csv results/test_spike --csv-full-history
# ============================================================

import hashlib
import random
import time

from fastapi import FastAPI

app = FastAPI(title="NT531 Mock Processing Service")

# Counters cho fake metrics
_request_count = 0
_total_duration = 0.0


@app.get("/health-check")
def health():
    """Liveness/readiness probe."""
    return {"status": "online"}


@app.post("/collect")
async def collect(data: dict):
    """
    Mock processing endpoint.
    Dùng CPU-bound hash loop thay vì sleep — giống behavior thật.
    Thời gian xử lý ~10-50ms tùy iterations.
    """
    global _request_count, _total_duration

    start = time.time()

    # CPU-bound: hash iterations (giả lập validate + classify vital signs)
    iterations = random.randint(3000, 15000)
    result = str(data).encode()
    for _ in range(iterations):
        result = hashlib.sha256(result).digest()

    duration = time.time() - start
    _request_count += 1
    _total_duration += duration

    return {
        "status": "received",
        "process_time_ms": round(duration * 1000, 2),
    }


@app.get("/metrics")
def metrics():
    """Fake Prometheus text format metrics."""
    return (
        f"# HELP http_request_total Total HTTP requests\n"
        f"# TYPE http_request_total counter\n"
        f'http_request_total{{method="POST",endpoint="/collect"}} {_request_count}\n'
        f"# HELP http_request_duration_seconds Request latency\n"
        f"# TYPE http_request_duration_seconds summary\n"
        f'http_request_duration_seconds_sum{{endpoint="/collect"}} {_total_duration:.4f}\n'
        f'http_request_duration_seconds_count{{endpoint="/collect"}} {_request_count}\n'
    )
