import time
from prometheus_api_client import PrometheusConnect
from prometheus_client import start_http_server, Gauge
from sklearn.linear_model import LinearRegression
import numpy as np

# ============================================================
# 1. CẤU HÌNH NỘI BỘ (INTERNAL K8S CONFIG)
# ============================================================
# Trỏ trực tiếp vào Service của Prometheus trong cluster
PROMETHEUS_URL = "http://100.97.201.48:9090"
pc = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# Metric thực tế lấy từ App của Quyên
QUERY_REAL_LOAD = 'sum(rate(request_execution_duration_seconds_count[1m]))'

# Khai báo Metric để KEDA đọc (Khớp với file proactive-scaler.yaml)
# Lưu ý: Gauge name phải là 'predicted_traffic_demand'
PREDICTED_LOAD = Gauge('predicted_traffic_demand', 'Dự báo tải trong 30s tới từ AI')
CURRENT_LOAD_GAUGE = Gauge('current_traffic_rate', 'Tải thực tế đo được')

def get_current_load():
    try:
        result = pc.custom_query(query=QUERY_REAL_LOAD)
        # Nếu có dữ liệu thì lấy giá trị, không thì trả về 0
        if result and len(result) > 0:
            return float(result[0]['value'][1])
    except Exception as e:
        print(f"[ERROR] Không thể lấy dữ liệu từ Prometheus: {e}")
    return 0.0

def run_controller():
    print("--- Proactive AI Controller đang chạy nội bộ (Cổng 9000) ---")
    history = []
    
    while True:
        try:
            curr = get_current_load()
            CURRENT_LOAD_GAUGE.set(curr)
            history.append(curr)
            
            # Cần ít nhất 5 điểm dữ liệu (50 giây) để bắt đầu dự báo xu hướng
            if len(history) > 5:
                # Chỉ lấy 10 điểm gần nhất để đảm bảo tính thời sự
                if len(history) > 10:
                    history = history[-10:]
                
                # Xây dựng mô hình hồi quy tuyến tính đơn giản
                X = np.array(range(len(history))).reshape(-1, 1)
                y = np.array(history)
                model = LinearRegression().fit(X, y)
                
                # Dự báo tải cho 30s tới (3 chu kỳ tiếp theo)
                # Công thức: y = ax + b -> Dự báo tại điểm (hiện tại + 3)
                prediction = model.predict([[len(history) + 3]])[0]
                prediction = max(0, float(prediction)) # Không để tải âm
                
                PREDICTED_LOAD.set(prediction)
                print(f"[AI] Thực tế: {curr:.2f} rps -> Dự báo (30s): {prediction:.2f} rps")
            else:
                print(f"[*] Đang tích lũy dữ liệu... ({len(history)}/5)")
                PREDICTED_LOAD.set(curr) # Tạm thời lấy tải thực tế làm dự báo
                
        except Exception as e:
            print(f"[ERROR] Lỗi logic AI: {e}")
            
        time.sleep(10) # Chu kỳ phân tích 10s theo kịch bản 3

if __name__ == '__main__':
    # Chạy HTTP Server tại cổng 9000 để Prometheus Scrape dữ liệu
    # Port 9000 phải khớp với containerPort trong file Deployment
    start_http_server(9000, addr='0.0.0.0')
    run_controller()
