import time
from prometheus_api_client import PrometheusConnect
from prometheus_client import start_http_server, Gauge
from sklearn.linear_model import LinearRegression
import numpy as np

# 1. Kết nối tới Prometheus (Dùng IP Tailscale của máy chính)
PROMETHEUS_URL = "http://100.97.201.48:9090" 
pc = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# 2. Khai báo Metric (Khớp với query trong KEDA)
PREDICTED_LOAD = Gauge('predicted_traffic_demand', 'Dự báo tải trong 30s tới')

def get_current_load():
    query = 'sum(rate(http_requests_total[1m]))'
    result = pc.custom_query(query=query)
    return float(result[0]['value'][1]) if result else 0

def run_controller():
    print("--- Proactive Controller đang chạy (Cổng 8001) ---")
    history = []
    while True:
        try:
            curr = get_current_load()
            history.append(curr)
            if len(history) > 5:
                history = history[-10:]
                X = np.array(range(len(history))).reshape(-1, 1)
                y = np.array(history)
                model = LinearRegression().fit(X, y)
                prediction = max(0, float(model.predict([[len(history) + 3]])[0]))
                PREDICTED_LOAD.set(prediction)
                print(f"[AI] Thực tế: {curr:.2f} -> Dự báo 30s tới: {prediction:.2f}")
            else:
                print(f"[*] Đang thu thập dữ liệu... ({len(history)}/5)")
                PREDICTED_LOAD.set(curr)
        except Exception as e:
            print(f"Lỗi: {e}")
        time.sleep(10)

if __name__ == '__main__':
    # QUAN TRỌNG: addr='0.0.0.0' để Prometheus có thể kết nối từ Cluster vào Host
    start_http_server(8001, addr='0.0.0.0')
    run_controller()
