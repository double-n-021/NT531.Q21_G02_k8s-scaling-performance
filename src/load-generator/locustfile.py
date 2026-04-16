# locustfile.py
# ============================================================
# NT531 Load Generator — 5 Traffic Profiles
# ============================================================
# Đồ án: Đánh giá hiệu năng các chiến lược scaling trên Kubernetes
# Mô phỏng thiết bị IoMT gửi dữ liệu sinh hiệu (HR, SpO2, BP)
#
# Usage:
#   # Interactive (debug — mở web UI):
#   locust -f locustfile.py --host http://192.168.1.100
#
#   # Headless — Stable profile:
#   PROFILE=stable locust -f locustfile.py --host http://192.168.1.100 \
#     --headless --users 20 --spawn-rate 20 --run-time 180s \
#     --csv results/stable_run1 --csv-full-history
#
#   # Headless — Spike profile (dùng LoadShape, KHÔNG cần --users):
#   PROFILE=spike locust -f locustfile.py --host http://192.168.1.100 \
#     --headless --csv results/spike_run1 --csv-full-history
#
#   # Windows PowerShell:
#   $env:PROFILE="spike"; $env:LOCUST_SEED="42"
#   locust -f locustfile.py --host http://localhost:8000 --headless `
#     --csv results/spike_run1 --csv-full-history
# ============================================================

import json
import math
import os
import random
import time

import yaml
from locust import HttpUser, LoadTestShape, between, events, task

# ── Config ──────────────────────────────────────────────────
CONFIG_PATH = os.environ.get("LOCUST_CONFIG", "config/default.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

PROFILE = os.environ.get("PROFILE", "stable")
ENDPOINT = CONFIG["target"]["endpoint"]

# Seed cho reproducibility — mỗi run đổi seed (base + run_id)
SEED = int(os.environ.get("LOCUST_SEED", "42"))
random.seed(SEED)


# ── User Class ──────────────────────────────────────────────
class VitalSignUser(HttpUser):
    """
    Mô phỏng 1 thiết bị IoMT gửi dữ liệu sinh hiệu.
    Mỗi user gửi ~1 req/s (wait_time 0.5–1.5s, trung bình 1s).
    Số concurrent users quyết định request rate (λ):
      20 users × 1 req/s/user = 20 req/s = λ_normal
    """

    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Khởi tạo device ID ngẫu nhiên."""
        self.device_id = f"iomt-{random.randint(1000, 9999)}"

    @task
    def send_vital_signs(self):
        """POST dữ liệu sinh hiệu — payload JSON nhẹ."""
        payload = {
            "device_id": self.device_id,
            "timestamp": time.time(),
            "vital_signs": {
                "heart_rate": random.randint(55, 130),
                "spo2": round(random.uniform(93.0, 100.0), 1),
                "blood_pressure": {
                    "systolic": random.randint(95, 170),
                    "diastolic": random.randint(55, 105),
                },
                "temperature": round(random.uniform(36.0, 39.5), 1),
            },
        }
        self.client.post(
            ENDPOINT,
            json=payload,
            name="/collect",  # Gộp tất cả requests dưới 1 tên trong stats
        )


# ── LoadShape ───────────────────────────────────────────────
class TrafficShape(LoadTestShape):
    """
    Custom LoadShape cho 4 profiles có shape phức tạp:
    - ramp, spike, spike_recovery: dùng stages (bậc thang)
    - oscillating: dùng sin wave

    Profile "stable" KHÔNG dùng LoadShape — chạy bằng --users/--spawn-rate.
    """

    def __init__(self):
        super().__init__()
        self.profile_name = PROFILE
        self.profile_config = CONFIG["profiles"].get(PROFILE, {})
        self.timeline = []

        if self.profile_name not in ("stable", "oscillating"):
            self._build_timeline()

    def _build_timeline(self):
        """Chuyển stages config thành timeline."""
        stages = self.profile_config.get("stages", [])
        elapsed = 0
        for stage in stages:
            elapsed += stage["duration"]
            self.timeline.append(
                {
                    "end_time": elapsed,
                    "users": stage["users"],
                    "spawn_rate": stage["spawn_rate"],
                }
            )

    def tick(self):
        """Trả về (user_count, spawn_rate) mỗi giây."""
        run_time = self.get_run_time()

        # Oscillating: sin wave
        if self.profile_name == "oscillating":
            return self._oscillating_tick(run_time)

        # Ramp / Spike / Spike-Recovery: staged timeline
        for stage in self.timeline:
            if run_time < stage["end_time"]:
                return (stage["users"], stage["spawn_rate"])

        # Hết timeline → dừng test
        return None

    def _oscillating_tick(self, run_time):
        """Sóng sin dao động giữa low_users và high_users."""
        cfg = self.profile_config
        total_duration = cfg.get("duration", 360)

        if run_time > total_duration:
            return None

        cycle = cfg.get("cycle_duration", 120)
        low = cfg.get("low_users", 20)
        high = cfg.get("high_users", 80)
        mid = (low + high) / 2
        amp = (high - low) / 2

        users = int(mid + amp * math.sin(2 * math.pi * run_time / cycle))
        return (max(1, users), 10)


# ── Global state cho timestamp logger ─────────────────────
_ts_file = None   # file handle cho raw timestamp log
_ts_path = None   # path để in ra lúc kết thúc


# ── Event Hooks ─────────────────────────────────────────────
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Ghi metadata khi test bắt đầu — dùng cho cross-reference với Prometheus."""
    global _ts_file, _ts_path

    meta = {
        "profile": PROFILE,
        "config_file": CONFIG_PATH,
        "seed": SEED,
        "start_epoch": time.time(),
        "start_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": environment.host,
        "calibration": CONFIG.get("calibration", {}),
    }

    csv_dir = CONFIG["experiment"]["csv_dir"]
    os.makedirs(csv_dir, exist_ok=True)

    # Ghi metadata JSON — tên file match với CSV prefix
    run_id = os.environ.get("RUN_ID", f"{PROFILE}_debug")
    meta_file = os.path.join(csv_dir, f"{run_id}_meta.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # ── Mở file raw timestamps (cho KS test / Q-Q plot kiểm chứng Poisson) ──
    # Mỗi dòng = 1 request: epoch_s (giây, 6 chữ số thập phân), name, response_time_ms, success
    _ts_path = os.path.join(csv_dir, f"{run_id}_timestamps.csv")
    _ts_file = open(_ts_path, "w", encoding="utf-8", buffering=1)  # line-buffered
    _ts_file.write("epoch_s,name,response_time_ms,success\n")

    print(f"[META] Test started: {meta['start_iso']}")
    print(f"[META] Profile: {PROFILE}, Seed: {SEED}")
    print(f"[META] Host: {environment.host}")
    print(f"[META] Metadata saved to: {meta_file}")
    print(f"[META] Raw timestamps → {_ts_path}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length,
               exception, context, start_time, **kwargs):
    """
    Fire sau mỗi request hoàn thành.
    Ghi timestamp chính xác đến microsecond → dùng tính inter-arrival times.

    Inter-arrival time Δtᵢ = tᵢ₊₁ − tᵢ (giây)
    Dùng start_time của Locust (thời điểm request được sinh ra) thay vì time.time()
    để đảm bảo ghi nhận đúng Arrival Process.
    """
    if _ts_file is None or _ts_file.closed:
        return
    ok = 0 if exception else 1
    rt = round(response_time, 2)              # ms, từ Locust
    _ts_file.write(f"{start_time:.6f},{name},{rt},{ok}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Đóng file timestamps và in thống kê."""
    global _ts_file
    stop_time = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"[META] Test stopped: {stop_time}")

    if _ts_file and not _ts_file.closed:
        _ts_file.flush()
        _ts_file.close()
        print(f"[META] Raw timestamps saved → {_ts_path}")
        print(f"[META] Use timestamps.csv for KS test (inter-arrival Poisson check)")
