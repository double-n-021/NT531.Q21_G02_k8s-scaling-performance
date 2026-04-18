# ============================================================
# PROACTIVE CONTROLLER (RULE-BASED EXTRAPOLATION VERSION)
# ============================================================

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

# ===== RULE PARAMETERS =====
EMA_ALPHA = 0.3
MAX_GROWTH_RATE = 1.5   # anti-spike (150%)
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
CURRENT_RPS = Gauge('current_rps', 'Raw traffic rate')
SMOOTHED_RPS = Gauge('smoothed_rps', 'EMA filtered load')
FUTURE_LOAD = Gauge('future_load', 'Extrapolated future load')
TARGET_PODS = Gauge('target_pods', 'Desired pods from controller')
CURRENT_PODS = Gauge('current_pods', 'Current pod count')

# ============================================================
# HELPERS
# ============================================================
def get_current_rps():
    try:
        result = pc.custom_query(query=QUERY_REAL_LOAD)
        if result:
            value = float(result[0]['value'][1])
            return max(0, value)  # RULE: không âm
    except Exception as e:
        print(f"[ERROR] Prometheus: {e}")
    return 0.0  # RULE: fallback an toàn


def get_current_pods():
    try:
        scale = apps_v1.read_namespaced_deployment_scale(
            DEPLOYMENT_NAME, NAMESPACE
        )
        return scale.status.replicas
    except Exception as e:
        print(f"[ERROR] K8s: {e}")
        return 0


def ema(prev, curr):
    return EMA_ALPHA * curr + (1 - EMA_ALPHA) * prev


# ============================================================
# MAIN LOOP
# ============================================================
def run():
    print("=== Rule-Based Extrapolation Controller Started ===")

    history = []

    while True:
        try:
            # =================================================
            # 1. CURRENT RPS (RAW)
            # =================================================
            curr_rps = get_current_rps()
            curr_pods = get_current_pods()

            CURRENT_RPS.set(curr_rps)
            CURRENT_PODS.set(curr_pods)

            # =================================================
            # 2. EMA SMOOTHING
            # =================================================
            if history:
                smoothed = ema(history[-1], curr_rps)
            else:
                smoothed = curr_rps

            SMOOTHED_RPS.set(smoothed)

            history.append(smoothed)
            if len(history) > MAX_HISTORY:
                history.pop(0)

            # =================================================
            # 3. EXTRAPOLATION (TREND EXTENSION)
            # =================================================
            if len(history) < MIN_HISTORY:
                future = smoothed
                print(f"[*] Collecting data... ({len(history)}/{MIN_HISTORY})")

            else:
                X = np.arange(len(history)).reshape(-1, 1)
                y = np.array(history)

                model = LinearRegression().fit(X, y)

                future_X = np.arange(len(history), len(history) + 3).reshape(-1, 1)
                preds = model.predict(future_X)

                future = float(np.mean(preds))

                # ===== RULE: ANTI-SPIKE =====
                last = history[-1]
                future = min(future, last * MAX_GROWTH_RATE)

                # ===== RULE: NON-NEGATIVE =====
                future = max(0, future)

            FUTURE_LOAD.set(future)

            # =================================================
            # 4. TARGET PODS (CORE RULE)
            # =================================================
            target = math.ceil(future / SCALING_THRESHOLD)

            target = max(MIN_PODS, min(target, MAX_PODS))

            # ===== RULE: ANTI-THRASHING =====
            if abs(target - curr_pods) < 1:
                target = curr_pods

            TARGET_PODS.set(target)

            print(
                f"[RULE] RPS={curr_rps:.2f} | Smooth={smoothed:.2f} | "
                f"Future={future:.2f} | Pods={curr_pods}->{target}"
            )

        except Exception as e:
            print(f"[ERROR] Main loop: {e}")

        time.sleep(SCRAPE_INTERVAL)


if __name__ == "__main__":
    start_http_server(9000)
    run()
