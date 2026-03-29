from fastapi import FastAPI, Request
import time
import uvicorn

app = FastAPI()

@app.post("/collect")
async def collect_data(request: Request):
    data = await request.json()
    
    # Giả lập delay xử lý của server (50ms)
    time.sleep(0.05) 
    
    return {"status": "ok", "message": "Received vital signs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Mock Server đang chạy tại: http://localhost:8000")
    print("👉 Endpoint nhận dữ liệu: http://localhost:8000/collect")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
