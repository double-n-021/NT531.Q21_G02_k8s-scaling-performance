# 🏥 Đánh giá Hiệu năng Mạng của các Chiến lược Scaling dựa trên Kubernetes trong Hệ thống Xử lý Dữ liệu Sinh hiệu IoMT

> **Học phần:** NT531 - Đánh giá hiệu năng hệ thống mạng máy tính  
> **Trường:** Đại học Công nghệ Thông tin, ĐHQG-HCM

Repository này cung cấp toàn bộ testbed (mã nguồn, cấu hình tự động hóa) và dữ liệu thực nghiệm phục vụ việc đánh giá hiệu năng tầng mạng (Network Performance) của các hệ thống Microservice y tế thời gian thực (Internet of Medical Things - IoMT) khi phải đối mặt với các kịch bản lưu lượng biến động mạnh.

---

## 📖 Tóm tắt Đồ án

Hệ thống theo dõi sức khỏe thời gian thực yêu cầu độ trễ (End-to-End Latency) cực thấp và nghiêm ngặt (P99 < 200ms) để không bỏ lỡ các cảnh báo nguy kịch của bệnh nhân. Khi có biến động số lượng thiết bị kết nối (ví dụ: giờ cao điểm nhập viện, khủng hoảng y tế), hệ thống cần nhanh chóng mở rộng tài nguyên. 

Đồ án này thực nghiệm, đo lường và so sánh hiệu năng của **3 chiến lược cấp phát tài nguyên** khi xử lý dòng traffic sinh hiệu y tế:
1. **Static Provisioning**: Cấp phát tĩnh (baseline k=2, 4, 6, 8 pods).
2. **Reactive Scaling (HPA)**: Mở rộng thụ động dựa trên ngưỡng CPU (CPU > 50%).
3. **Proactive Scaling (KEDA + Custom Controller)**: Mở rộng chủ động, dự đoán xu hướng nghẽn cổ chai sắp xảy ra để scale pod trước khi Latency tăng vọt.

Đặc biệt, đồ án được chiếu đối với **mô hình lý thuyết hàng đợi M/G/k (Xấp xỉ Kimura)** và tích hợp kỹ thuật **Chaos Engineering (LitmusChaos)** để đánh giá khả năng phục hồi (MTTR) khi một lượng lớn Pod xử lý rớt mạng đột ngột.

---

## 📂 Tổ chức Thư mục (Project Structure)

```text
├── src/                        # 💻 Mã nguồn Service & Custom Tools
│   ├── target-app/             # Ứng dụng SUT (FastAPI + Prometheus metrics + Dual histogram)
│   ├── load-generator/         # Kịch bản tải Locust (Stable, Ramp, Spike, Oscillating)
│   └── proactive-controller/   # Custom Controller Python tính toán và trigger KEDA
│
├── deploy/                     # ☸️ Kubernetes Manifests (k3s / AKS)
│   ├── infrastructure/         # Scripts khởi tạo testbed (Terraform/Ansible)
│   ├── observability/          # Stack giám sát (Prometheus, Grafana, Metrics Server)
│   ├── chaos/                  # Kịch bản LitmusChaos: Kill 50% Pods
│   └── strategies/             # Manifests cho 3 chiến lược: Static, HPA, KEDA
│
├── scripts/                    # 🛠️ Bộ kịch bản Tự động hóa Thực nghiệm
│   ├── verified_reset.sh       # Script giám sát hệ thống Drain Queue & hạ tải xuống Zero
│   └── run_experiment.sh       # Trigger quét ma trận kịch bản (170 runs)
│
├── data/                       # 📊 Dữ liệu thô (Raw metrics & Locust output)
│   ├── kb0_calibration/        # Tìm tham số M/G/k và chứng minh giả định Poisson
│   ├── kb1_static/             # Kết quả chạy Baseline
│   ├── kb2_reactive/           # Kết quả độ trễ HPA
│   ├── kb3_proactive/          # Kết quả độ trễ KEDA
│   ├── kb3f_chaos/             # Fault-injection vs MTTR data
│   └── kb4_sensitivity/        # Đánh giá Scrape interval trade-off (5s vs 30s)
│
├── notebooks/                  # 📓 Phân tích thống kê & Biểu đồ (Jupyter)
└── docs/                       # 📝 Slides, báo cáo, và Screenshots Evidence
```

---

## ⚡ Các Chỉ số Đo lường Chính (KPIs)

- **End-to-end Latency (P50/P95/P99):** Độ trễ tổng thể của gói tin trên mạng lưới.
- **Queueing Delay:** Đo trực tiếp từ trong luồng request chờ xử lý.
- **Throughput (req/s) & Error Rate (%):** Khả năng chịu tải trước khi dội ngược request 503.
- **MTTR (Mean Time To Recovery):** Thời gian đưa P99 Latency về lại dưới 200ms sau cú sốc (Spike/Chaos).
- **SLO Violation Count:** Số lượng data point bị vượt ngưỡng an toàn y tế trong đợt tải.

---

## 🚀 Hướng dẫn Cài đặt Nhanh (Quick Start)

**1. Yêu cầu hệ thống:**
- Một cụm Kubernetes đang chạy (Khuyến nghị dùng `k3s`). Ưu tiên 3 nodes, môi trường sạch.
- Python 3.10+ (để chạy Locust và Data Analysis).
- Helm & kubectl.

**2. Khởi tạo Kịch bản Tải (Load Generation):**
Thay vì dựng cả cụm k8s, bạn có thể kiểm tra trước luồng traffic sinh hiệu mô phỏng bằng cách bật Mock Server:
```bash
cd src/load-generator
pip install -r requirements.txt
python mock_server.py
```
Mở một Terminal khác để bắn tải mô phỏng "Spike" (tăng vọt lên 100 thiết bị):
```bash
# Trên Windows PowerShell
$env:PROFILE="spike"; locust -f locustfile.py --host http://localhost:8000 --headless
```

---

## 👥 Nhóm Thực hiện (Nhóm 02)

- Bùi Đăng Nhật Nguyên (23521037)
- Nguyễn Minh Quyền (23521325)
- Võ Trung Kiên (23520809)
