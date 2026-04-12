from fastapi import FastAPI, Request
import time
import math
import uvicorn

app = FastAPI()

def execute_cpu_intensive_task(iterations=200_000):
    result = 0
    for i in range(iterations):
        result += math.sqrt(i)
    return result

@app.post("/collect")
def collect_data(request: Request):
    # Vắt kiệt CPU thay vì ngủ đông
    execute_cpu_intensive_task()
    
    return {"status": "ok", "message": "Received vital signs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Mock Server đang chạy tại: http://localhost:8000")
    print("👉 Endpoint nhận dữ liệu: http://localhost:8000/collect")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
