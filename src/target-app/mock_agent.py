from prometheus_client import start_http_server, Gauge
import time
import random

# Tạo một metric tên là predicted_traffic_demand
PREDICTED_LOAD = Gauge('predicted_traffic_demand', 'Dự báo lưu lượng từ AI Agent')

if __name__ == '__main__':
    # Chạy server metrics tại cổng 8001
    start_http_server(8001)
    print("AI Agent đang gửi dự báo tại port 8001...")
    
    while True:
        # Giả lập AI dự báo: 
        # Tải thấp (dưới 6): Pod đứng yên (2)
        # Tải cao (trên 12): Pod sẽ tăng
        val = random.choice([3, 5, 15, 20]) 
        PREDICTED_LOAD.set(val)
        print(f"AI Agent dự báo tải sắp tới là: {val}")
        time.sleep(15)
