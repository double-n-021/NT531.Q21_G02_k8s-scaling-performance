from prometheus_client import start_http_server, Gauge
import time
import random

# Tạo metric dự báo tải (Predicted Load)
PREDICTED_LOAD = Gauge('predicted_traffic_demand', 'Dự báo lưu lượng từ AI Agent')

if __name__ == '__main__':
    # Chạy server metrics tại cổng 8001, lắng nghe mọi IP (0.0.0.0)
    start_http_server(8001, addr='0.0.0.0')
    print("AI Agent đang phát tín hiệu dự báo tại port 8001...")
    
    while True:
        # Giả lập AI: Lúc thì dự báo tải thấp (3), lúc thì tải cực cao (20)
        # Nếu val > 6 (threshold của bạn), Pod sẽ tự tăng!
        val = random.choice([3, 5, 12, 18, 25]) 
        PREDICTED_LOAD.set(val)
        print(f"--- AI DỰ BÁO: Tải sắp tới sẽ là {val} units ---")
        time.sleep(15) # 15 giây đổi dự báo một lần
