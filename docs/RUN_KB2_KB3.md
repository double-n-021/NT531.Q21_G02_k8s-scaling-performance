# Hướng dẫn chạy KB2 (HPA) và KB3 (KEDA + metric dự báo)

Hai kịch bản **không chạy song song** trên cùng một `Deployment/target-app`: mỗi lần chỉ bật **một** cơ chế scale (HPA *hoặc* KEDA). Locust chỉ phát tải; bạn tự chuyển manifest cluster trước khi benchmark.

**Giả định:**

- Namespace ứng dụng: `nt531-env`
- Namespace monitoring (Prometheus Operator): `monitoring`
- Đường dẫn manifest trong repo: `deploy/...`
- Đã cài **Metrics Server** (cho HPA) và **KEDA** (cho KB3).

---

## 0. Kiểm tra nhanh trước khi làm bất cứ bước nào

```bash
kubectl get nodes
kubectl get deploy,svc -n nt531-env
kubectl top pods -n nt531-env
```

Nếu `kubectl top` lỗi → cài/fix Metrics Server trước khi chạy KB2.

Tìm đúng tên Service Prometheus (để KB3 query được):

```bash
kubectl get svc -n monitoring
```

- Nếu thấy dạng `prometheus-kube-prometheus-prometheus` → sửa `serverAddress` trong `deploy/strategies/03-proactive/proactive-scaler.yaml` thành  
  `http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090`
- Nếu đúng `monitoring-kube-prometheus-prometheus` → giữ nguyên như file hiện tại.

---

## KB2 — Reactive scaling (Kubernetes HPA)

### Bước 1 — Tắt KEDA (nếu đang bật)

KEDA tạo HPA phụ; tránh chồng chéo với HPA “tay” của bạn.

```bash
kubectl delete scaledobject.keda.sh -n nt531-env target-app-proactive --ignore-not-found
kubectl delete hpa -n nt531-env -l app.kubernetes.io/managed-by=keda-operator --ignore-not-found
```

### Bước 2 — Áp dụng HPA reactive

Từ thư mục gốc repo:

```bash
kubectl apply -f deploy/strategies/02-reactive/hpa-reactive.yaml
```

### Bước 3 — Xác nhận

```bash
kubectl get hpa -n nt531-env
kubectl describe hpa -n nt531-env target-app-reactive
```

Khi bắn tải (Locust), quan sát `REPLICAS` / `TARGETS` thay đổi.

### Bước 4 — Phát tải (Locust)

Ví dụ (Linux / Git Bash), thay `HOST` bằng URL Ingress NodePort của bạn:

```bash
cd src/load-generator
export LOCUST_CONFIG=config/k2.yaml
locust -f locustfile.py --host "http://<IP_INGRESS>:<PORT>" --headless \
  --users 1 --spawn-rate 1 --run-time 300s \
  --csv results/hpa_kb2_smoke --csv-full-history
```

Hoặc dùng script suite (cần bash):

```bash
bash scripts/run_benchmark.sh hpa_kb2 spike 1 "http://<IP_INGRESS>:<PORT>" 180
```

**Profile `stable`:** trong `locustfile.py`, `stable` trả `None` từ LoadShape → bắt buộc truyền `--users` / `--spawn-rate` như trên. Các profile khác có thể chỉ cần `PROFILE=spike` + `--run-time`.

---

## KB3 — Proactive scaling (KEDA + Prometheus + mock `predicted_traffic_demand`)

### Bước 1 — Tắt HPA “standalone” của KB2

```bash
kubectl delete hpa -n nt531-env target-app-reactive --ignore-not-found
```

### Bước 2 — Triển khai mock exporter + ServiceMonitor scrape

```bash
kubectl apply -f deploy/strategies/03-proactive/mock-predicted-load.yaml
kubectl apply -f deploy/strategies/03-proactive/servicemonitor-ai-mock.yaml
```

Đợi pod mock Running:

```bash
kubectl rollout status -n nt531-env deploy/ai-mock-predictor
```

### Bước 3 — Prometheus đã có metric chưa

Port-forward (hoặc mở UI Prometheus), chạy PromQL:

```promql
sum(predicted_traffic_demand)
```

- Nếu **empty / no data**: label `release: monitoring` của `ServiceMonitor` không khớp Prometheus của bạn → sửa label trong `servicemonitor-ai-mock.yaml` cho giống các `ServiceMonitor` khác đang được scrape (xem `kubectl get servicemonitor -A --show-labels`).

### Bước 4 — Áp ScaledObject KEDA

```bash
kubectl apply -f deploy/strategies/03-proactive/proactive-scaler.yaml
```

KEDA sẽ tạo HPA phụ (managed-by KEDA):

```bash
kubectl get scaledobject.keda.sh -n nt531-env
kubectl get hpa -n nt531-env
kubectl describe scaledobject.keda.sh -n nt531-env target-app-proactive
```

### Bước 5 — Phát tải

Giống KB2; đặt prefix strategy cho dễ lưu file, ví dụ:

```bash
bash scripts/run_benchmark.sh keda_kb3 spike 1 "http://<IP_INGRESS>:<PORT>" 180
```

---

## Chuyển từ KB3 về KB2 (hoặc ngược lại)

Luôn: **gỡ scaler cũ → apply scaler mới → chờ ổn định → chạy Locust**.

---

## Windows PowerShell (gợi ý Locust)

```powershell
cd F:\HK_VI_2026\NT531_Danh-gia-hieu-nang-he-thong-mang-may-tinh\_repo_clone\src\load-generator
$env:LOCUST_CONFIG = "config\k2.yaml"
$env:PROFILE = "spike"
locust -f locustfile.py --host "http://<IP>:<PORT>" --headless --csv results/kb2_spike_smoke --csv-full-history
```

---

## Sự cố thường gặp

| Hiện tượng | Hướng xử lý |
|------------|-------------|
| HPA `unknown` / không có metrics | Cài Metrics Server; kiểm tra `resources.requests.cpu` của pod `target-app` |
| KEDA `Failed to execute prometheus query` | Sửa `serverAddress` đúng svc Prometheus; kiểm tra network policy |
| `sum(predicted_traffic_demand)` không có điểm | Sửa label ServiceMonitor; đợi ~1–2 phút scrape; kiểm tra Service `ai-mock-predictor` port `metrics` |
| Hai HPA cùng scale một Deployment | Xóa HPA/ScaledObject thừa như các bước trên |
