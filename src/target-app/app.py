import sys
import time
import math
from prometheus_client import Histogram, Gauge, Counter, generate_latest
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

app = FastAPI()

# 1. Khai báo Metrics cho Prometheus
REQUEST_QUEUEING_TIME = Histogram('request_queueing_duration_seconds', 'Time')
REQUEST_EXECUTION_TIME = Histogram('request_execution_duration_seconds', 'Time')
REQUEST_TOTAL_TIME = Histogram('request_total_duration_seconds', 'Total')
ACTIVE_REQUESTS = Gauge('active_requests', 'Active')
HTTP_REQUESTS_TOTAL = Counter('http_requests_total', 'Total', ['method', 'endpoint', 'code'])

class VitalSigns(BaseModel):
    heart_rate: int
    spo2: float
    blood_pressure: dict
    temperature: float

class Payload(BaseModel):
    device_id: str
    timestamp: float
    vital_signs: VitalSigns

@app.middleware("http")
async def add_start_time(request: Request, call_next):
    request.state.queue_start_time = time.time()
    response = await call_next(request)
    HTTP_REQUESTS_TOTAL.labels(method=request.method, endpoint=request.url.path, code=response.status_code).inc()
    return response

def execute_cpu_intensive_task(iterations=2_000_000):
    result = 0
    for i in range(iterations):
        result += math.sqrt(i)
    return result

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type="text/plain")

@app.post("/collect")
def collect_vital_signs(payload: Payload, request: Request):
    execution_start_time = time.time()
    queueing_delay = execution_start_time - request.state.queue_start_time
    
    with ACTIVE_REQUESTS.track_inprogress():
        execute_cpu_intensive_task() 
        execution_time = time.time() - execution_start_time
        
        REQUEST_QUEUEING_TIME.observe(queueing_delay)
        REQUEST_EXECUTION_TIME.observe(execution_time)
        REQUEST_TOTAL_TIME.observe(queueing_delay + execution_time)

        # CHIÊU CUỐI: Ghi thẳng vào stderr (không bị buffer, không bị Uvicorn nuốt)
        sys.stderr.write(f"RAW_DATA | {payload.device_id} | execution_time: {execution_time:.6f}s | queueing_delay: {queueing_delay:.6f}s\n")
        sys.stderr.flush()
        
        return {
            "status": "success", 
            "device": payload.device_id,
            "metrics": {
                "queueing_delay_ms": round(queueing_delay * 1000, 2),
                "execution_time_ms": round(execution_time * 1000, 2)
            }
        }