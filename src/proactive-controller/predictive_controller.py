import time, math
import numpy as np
from prometheus_api_client import PrometheusConnect
from prometheus_client import start_http_server
from sklearn.linear_model import LinearRegression
from kubernetes import client, config
from threading import Thread

import metrics
from grpc_server import start_grpc

# --- CONFIG ---
PROMETHEUS_URL = "http://100.99.156.17:9090"
QUERY_REAL_LOAD = 'sum(rate(http_requests_total[2m]))'

NAMESPACE, DEPLOYMENT_NAME = "nt531-env", "target-app"

SCALING_THRESHOLD, MIN_PODS, MAX_PODS = 4.0, 2, 8
EMA_ALPHA, MAX_GROWTH_RATE = 0.3, 1.5
MIN_HISTORY, MAX_HISTORY = 6, 12

pc = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

try:
    config.load_incluster_config()
except:
    config.load_kube_config()

apps_v1 = client.AppsV1Api()


# =========================
# HELPER
# =========================
def ema(prev, curr):
    return EMA_ALPHA * curr + (1 - EMA_ALPHA) * prev


# =========================
# MAIN LOOP
# =========================
def run():
    print("=== Proactive Controller Loop Started ===", flush=True)

    history = []

    while True:
        try:
            # ======================================
            # 1. CURRENT RPS (RAW)
            # ======================================
            res = pc.custom_query(query=QUERY_REAL_LOAD)
            curr_rps = float(res[0]['value'][1]) if res else 0.0

            scale = apps_v1.read_namespaced_deployment_scale(
                DEPLOYMENT_NAME, NAMESPACE
            )
            curr_pods = scale.status.replicas

            # export raw
            metrics.CURRENT_RPS.set(curr_rps)

            # ======================================
            # 2. SMOOTHING (EMA)
            # ======================================
            if history:
                smoothed = ema(history[-1], curr_rps)
            else:
                smoothed = curr_rps

            history.append(smoothed)
            if len(history) > MAX_HISTORY:
                history.pop(0)

            # ⭐ EXPORT SMOOTHED (BẠN ĐANG THIẾU CHỖ NÀY)
            metrics.SMOOTHED_RPS.set(smoothed)

            # ======================================
            # 3. EXTRAPOLATION (TREND)
            # ======================================
            if len(history) >= MIN_HISTORY:
                X = np.arange(len(history)).reshape(-1, 1)
                model = LinearRegression().fit(X, np.array(history))

                future_points = np.arange(
                    len(history), len(history) + 3
                ).reshape(-1, 1)

                preds = model.predict(future_points)
                future = float(np.mean(preds))

                # Anti-spike
                future = min(future, smoothed * MAX_GROWTH_RATE)

                # Non-negative
                future = max(0, future)
            else:
                future = smoothed

            metrics.FUTURE_LOAD.set(future)

            # ======================================
            # 4. TARGET PODS
            # ======================================
            target = math.ceil(future / SCALING_THRESHOLD)
            target = max(MIN_PODS, min(target, MAX_PODS))

            # Anti-thrashing
            if abs(target - curr_pods) < 1:
                target = curr_pods

            metrics.TARGET_PODS.set(target)

            # ======================================
            # 5. SHARED STATE (gRPC)
            # ======================================
            metrics.LATEST_PREDICTION = future
            metrics.LATEST_TARGET_PODS = target

            # ======================================
            # LOG
            # ======================================
            print(
                f"[CONTROLLER] RPS={curr_rps:.2f} | Smooth={smoothed:.2f} | "
                f"Future={future:.2f} | Pods={curr_pods}->{target}",
                flush=True
            )

        except Exception as e:
            print(f"[ERROR] {e}", flush=True)

        time.sleep(10)


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    start_http_server(9000)
    Thread(target=start_grpc, daemon=True).start()
    run()
