from prometheus_client import Histogram, Gauge, generate_latest
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import time
import math

app = FastAPI()

# 1. Khai báo Dual Histogram (Đo bóc tách Queueing vs Execution)
REQUEST_QUEUEING_TIME = Histogram(
    'request_queueing_duration_seconds', 
    'Time spent waiting in FastAPI thread pool queue'
)
REQUEST_EXECUTION_TIME = Histogram(
    'request_execution_duration_seconds', 
    'Time spent actually processing the CPU task'
)
REQUEST_TOTAL_TIME = Histogram(
    'request_total_duration_seconds', 
    'Total time End-to-End (Queueing + Execution)'
)
ACTIVE_REQUESTS = Gauge(
    'active_requests', 
    'Number of requests currently being processed by thread pool'
)

# 2. Định nghĩa cấu trúc Payload mô phỏng dữ liệu y sinh từ Locust
class VitalSigns(BaseModel):
    heart_rate: int
    spo2: float
    blood_pressure: dict
    temperature: float

class Payload(BaseModel):
    device_id: str
    timestamp: float
    vital_signs: VitalSigns

# Middleware 1: Ghi nhận thời gian yêu cầu vừa đập vào cửa ngõ FastAPI
@app.middleware("http")
async def add_start_time(request: Request, call_next):
    # Thời điểm sự kiện mạng bắt đầu được event-loop tiếp nhận
    request.state.queue_start_time = time.time()
    response = await call_next(request)
    return response

# Hàm giả lập CPU-Bound (Sử dụng vòng lặp để vắt kiệt CPU)
def execute_cpu_intensive_task(iterations=2_000_000):
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

# 3. Đổi thành @app.post("/collect") cho khớp với kịch bản Locust
# CHÚ Ý: KHÔNG CÓ `async` để đảm bảo FastAPI đẩy hàm này vào Thread Pool gây nghẽn thật
@app.post("/collect") 
def collect_vital_signs(payload: Payload, request: Request):
    # Ngay khi Thread Pool có slot rảnh và bắt đầu chạy hàm, ta đo thời điểm
    execution_start_time = time.time()
    
    # Tính Queueing Delay: Thời gian chờ trong rổ
    queueing_delay = execution_start_time - request.state.queue_start_time
    REQUEST_QUEUEING_TIME.observe(queueing_delay)
    
    with ACTIVE_REQUESTS.track_inprogress():
        # Xử lý tải giả lập CPU Bound
        execute_cpu_intensive_task() 
        
        # Tính Execution Time: Thời gian thực tế để tính toán mảng
        execution_time = time.time() - execution_start_time
        REQUEST_EXECUTION_TIME.observe(execution_time)
        
        # Tính Total Của Toàn bộ Quá trình
        REQUEST_TOTAL_TIME.observe(queueing_delay + execution_time)
        
        return {
            "status": "success", 
            "device": payload.device_id,
            "metrics": {
                "queueing_delay_ms": round(queueing_delay * 1000, 2),
                "execution_time_ms": round(execution_time * 1000, 2)
            }
        }
