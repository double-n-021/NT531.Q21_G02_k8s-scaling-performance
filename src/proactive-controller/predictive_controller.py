import time
import math
import numpy as np
from prometheus_api_client import PrometheusConnect
from prometheus_client import start_http_server, Gauge
from sklearn.linear_model import LinearRegression
from kubernetes import client, config

# ============================================================
# CONFIG
# ============================================================
PROMETHEUS_URL = "http://100.99.156.17:9090"
QUERY_REAL_LOAD = 'sum(rate(http_requests_total[2m]))'

NAMESPACE = "nt531-env"
DEPLOYMENT_NAME = "target-app"

SCALING_THRESHOLD = 6.0
MIN_PODS = 2
MAX_PODS = 6

SCRAPE_INTERVAL = 10

# Smoothing
EMA_ALPHA = 0.3

# Anti-spike
MAX_GROWTH_RATE = 1.5  # max +50% mỗi step

# History
MIN_HISTORY = 6
MAX_HISTORY = 12

# ============================================================
# INIT
# ============================================================
pc = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

apps_v1 = client.AppsV1Api()

# ============================================================
# METRICS EXPORT
# ============================================================
PREDICTED_LOAD = Gauge('predicted_traffic_demand', 'AI predicted traffic')
CURRENT_LOAD = Gauge('current_traffic_rate', 'Current traffic rate')
EXPECTED_PODS = Gauge('predicted_replicas_count', 'Predicted pod count')
CURRENT_PODS = Gauge('current_replicas_count', 'Current pod count')

# ============================================================
# HELPERS
# ============================================================
def get_current_load():
    try:
        result = pc.custom_query(query=QUERY_REAL_LOAD)
        if result:
            return float(result[0]['value'][1])
    except Exception as e:
        print(f"[ERROR] Prometheus query: {e}")
    return 0.0


def get_current_pods():
    try:
        scale = apps_v1.read_namespaced_deployment_scale(
            DEPLOYMENT_NAME, NAMESPACE
        )
        return scale.status.replicas
    except Exception as e:
        print(f"[ERROR] K8s API: {e}")
        return 0


def ema(prev, curr, alpha=EMA_ALPHA):
    return alpha * curr + (1 - alpha) * prev


# ============================================================
# MAIN LOOP
# ============================================================
def run():
    print("=== Proactive Controller v2 Started ===", flush=True)

    history = []

    while True:
        try:
            curr_rps = get_current_load()
            curr_pods = get_current_pods()

            CURRENT_LOAD.set(curr_rps)
            CURRENT_PODS.set(curr_pods)

            # ===== SMOOTHING =====
            if history:
                smoothed = ema(history[-1], curr_rps)
            else:
                smoothed = curr_rps

            history.append(smoothed)

            if len(history) > MAX_HISTORY:
                history.pop(0)

            # ===== CHƯA ĐỦ DATA =====
            if len(history) < MIN_HISTORY:
                prediction = smoothed
                print(f"[*] Collecting data... ({len(history)}/{MIN_HISTORY})")

            else:
                # ===== REGRESSION =====
                X = np.array(range(len(history))).reshape(-1, 1)
                y = np.array(history)

                model = LinearRegression().fit(X, y)

                # multi-step prediction (3 bước tương lai)
                future_X = np.array(
                    range(len(history), len(history) + 3)
                ).reshape(-1, 1)

                preds = model.predict(future_X)
                prediction = float(np.mean(preds))

                # ===== ANTI-SPIKE =====
                last = history[-1]
                prediction = min(prediction, last * MAX_GROWTH_RATE)

                # ===== NON-NEGATIVE =====
                prediction = max(0, prediction)

            # ===== CALCULATE PODS =====
            predicted_pods = math.ceil(prediction / SCALING_THRESHOLD)
            predicted_pods = max(MIN_PODS, min(predicted_pods, MAX_PODS))

            # ===== ANTI-THRASHING =====
            if abs(predicted_pods - curr_pods) < 1:
                predicted_pods = curr_pods

            # ===== EXPORT METRICS =====
            PREDICTED_LOAD.set(prediction)
            EXPECTED_PODS.set(predicted_pods)

            print(
                f"[AI] RPS={curr_rps:.2f} | Smooth={smoothed:.2f} | "
                f"Pred={prediction:.2f} | Pods={curr_pods}->{predicted_pods}",
                flush=True
            )

        except Exception as e:
            print(f"[ERROR] Main loop: {e}", flush=True)

        time.sleep(SCRAPE_INTERVAL)


# ============================================================
# ENTRYPOINT
# ============================================================
if __name__ == "__main__":
    start_http_server(9000)
    run()
