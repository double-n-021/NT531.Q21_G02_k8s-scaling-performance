from prometheus_client import Gauge

# Prometheus Gauges
CURRENT_RPS = Gauge('current_rps', 'Raw traffic rate')
CURRENT_PODS = Gauge('current_pods_count', 'Actual pod count')
SMOOTHED_RPS = Gauge('smoothed_rps', 'RPS after EMA')
FUTURE_LOAD = Gauge('predicted_traffic_demand', 'AI predicted load')
TARGET_PODS = Gauge('predicted_replicas_count', 'AI recommended pod count')

# Biến global để gRPC server đọc được
LATEST_PREDICTION = 0.0
LATEST_TARGET_PODS = 2
