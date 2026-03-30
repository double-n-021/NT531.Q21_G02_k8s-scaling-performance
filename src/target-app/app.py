from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
import time
import math

app = FastAPI()

# Khai báo Metrics
REQUEST_TIME = Histogram('request_processing_seconds', 'Time spent processing request')
ACTIVE_REQUESTS = Gauge('active_requests', 'Number of requests currently being processed')

def execute_cpu_intensive_task(iterations=2_000_000): # Giảm xuống xíu để test cho nhanh
    result = 0
    for i in range(iterations):
        result += math.sqrt(i)
    return result

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

@app.get("/")
def root():
    return {"message": "Target App is running"}

# ĐỔI THÀNH @app.get để khớp với lệnh ab
# BỎ async để FastAPI chạy nó trong thread pool, không làm treo server metrics
@app.get("/process") 
@REQUEST_TIME.time() 
def process_data():
    # Sử dụng track_inprogress() bên trong hàm xử lý
    with ACTIVE_REQUESTS.track_inprogress():
        execute_cpu_intensive_task() 
        return {"status": "processing_finished"}
