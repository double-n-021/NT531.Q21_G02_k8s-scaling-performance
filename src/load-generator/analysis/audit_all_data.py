#!/usr/bin/env python3
"""Comprehensive audit: extract ALL metrics from ALL stats.csv files."""
import pandas as pd
import glob, os

def extract_aggregated(csv_path):
    """Extract Aggregated row from a Locust stats.csv file."""
    try:
        df = pd.read_csv(csv_path)
        agg = df[df["Name"] == "Aggregated"]
        if agg.empty:
            return None
        row = agg.iloc[0]
        return {
            "Request Count": int(row["Request Count"]),
            "Failure Count": int(row["Failure Count"]),
            "RPS": round(float(row["Requests/s"]), 2),
            "Avg (ms)": round(float(row["Average Response Time"]), 1),
            "P50 (ms)": int(row["50%"]),
            "P95 (ms)": int(row["95%"]),
            "P99 (ms)": int(row["99%"]),
            "Max (ms)": round(float(row["Max Response Time"]), 1),
        }
    except Exception as e:
        return {"Error": str(e)}

def check_history(csv_path):
    """Check if a history CSV has real data (>2 rows)."""
    try:
        df = pd.read_csv(csv_path)
        return len(df) > 2
    except:
        return False

# ── KB1: Static Baseline ──────────────────────────────────────────
print("=" * 80)
print("KB1 — STATIC BASELINE (math_profile/)")
print("=" * 80)
for k in [2, 4, 8]:
    for traffic in ["stable", "ramp", "spike_recovery"]:
        pattern = f"data/math_profile/static-k{k}_{traffic}_run*_stats.csv"
        files = sorted(glob.glob(pattern))
        if not files:
            print(f"\n  K={k} | {traffic:16s} | ❌ NO DATA")
            continue
        print(f"\n  K={k} | {traffic:16s} | {len(files)} run(s)")
        for f in files:
            metrics = extract_aggregated(f)
            run = os.path.basename(f).split("_stats")[0].split("run")[-1]
            if metrics and "Error" not in metrics:
                print(f"    run{run}: Reqs={metrics['Request Count']:5d}  Fails={metrics['Failure Count']:3d}"
                      f"  RPS={metrics['RPS']:5.2f}  Avg={metrics['Avg (ms)']:7.1f}  "
                      f"P50={metrics['P50 (ms)']:5d}  P95={metrics['P95 (ms)']:5d}  P99={metrics['P99 (ms)']:5d}  Max={metrics['Max (ms)']:8.1f}")
            else:
                print(f"    run{run}: ⚠️ {metrics}")
        # Check history files
        hist_pattern = f"data/math_profile/static-k{k}_{traffic}_run*_stats_history.csv"
        hist_files = sorted(glob.glob(hist_pattern))
        valid_hist = [f for f in hist_files if check_history(f)]
        print(f"    → History files: {len(hist_files)} total, {len(valid_hist)} valid (>2 rows)")

# ── KB2: Reactive HPA ─────────────────────────────────────────────
print("\n" + "=" * 80)
print("KB2 — REACTIVE HPA (kb2_reactive/hpa/)")
print("=" * 80)
for traffic in ["stable", "ramp", "spike_recovery"]:
    pattern = f"data/kb2_reactive/hpa/reactive-hpa_{traffic}_run*_stats.csv"
    files = sorted(glob.glob(pattern))
    # Also check old naming
    if not files and traffic == "spike_recovery":
        old = glob.glob("data/kb2_reactive/hpa/hpa_reactive_stats.csv")
        if old:
            files = old
    if not files:
        print(f"\n  {traffic:16s} | ❌ NO DATA")
        continue
    print(f"\n  {traffic:16s} | {len(files)} run(s)")
    for f in files:
        metrics = extract_aggregated(f)
        name = os.path.basename(f)
        if metrics and "Error" not in metrics:
            print(f"    {name}: Reqs={metrics['Request Count']:5d}  Fails={metrics['Failure Count']:3d}"
                  f"  RPS={metrics['RPS']:5.2f}  Avg={metrics['Avg (ms)']:7.1f}  "
                  f"P50={metrics['P50 (ms)']:5d}  P95={metrics['P95 (ms)']:5d}  P99={metrics['P99 (ms)']:5d}  Max={metrics['Max (ms)']:8.1f}")
        else:
            print(f"    {name}: ⚠️ {metrics}")
    hist_pattern = f"data/kb2_reactive/hpa/reactive-hpa_{traffic}_run*_stats_history.csv"
    hist_files = sorted(glob.glob(hist_pattern))
    valid_hist = [f for f in hist_files if check_history(f)]
    print(f"    → History files: {len(hist_files)} total, {len(valid_hist)} valid")

# ── KB3: Proactive AI ─────────────────────────────────────────────
print("\n" + "=" * 80)
print("KB3 — PROACTIVE AI (kb3_proactive/)")
print("=" * 80)
for traffic in ["stable", "ramp", "spike_recovery"]:
    pattern = f"data/kb3_proactive/proactive-keda_{traffic}_run*_stats.csv"
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"\n  {traffic:16s} | ❌ NO DATA")
        continue
    print(f"\n  {traffic:16s} | {len(files)} run(s)")
    for f in files:
        metrics = extract_aggregated(f)
        run = os.path.basename(f).split("_stats")[0].split("run")[-1]
        if metrics and "Error" not in metrics:
            print(f"    run{run}: Reqs={metrics['Request Count']:5d}  Fails={metrics['Failure Count']:3d}"
                  f"  RPS={metrics['RPS']:5.2f}  Avg={metrics['Avg (ms)']:7.1f}  "
                  f"P50={metrics['P50 (ms)']:5d}  P95={metrics['P95 (ms)']:5d}  P99={metrics['P99 (ms)']:5d}  Max={metrics['Max (ms)']:8.1f}")
        else:
            print(f"    run{run}: ⚠️ {metrics}")
    hist_pattern = f"data/kb3_proactive/proactive-keda_{traffic}_run*_stats_history.csv"
    hist_files = sorted(glob.glob(hist_pattern))
    valid_hist = [f for f in hist_files if check_history(f)]
    print(f"    → History files: {len(hist_files)} total, {len(valid_hist)} valid")

# ── KB4: Sensitivity ──────────────────────────────────────────────
print("\n" + "=" * 80)
print("KB4 — SENSITIVITY (kb4_sensitivity/)")
print("=" * 80)
for thresh in ["2.0", "6.0"]:
    pattern = f"data/kb4_sensitivity/threshold_{thresh}/proactive-keda_ramp_run*_stats.csv"
    files = sorted(glob.glob(pattern))
    print(f"\n  Threshold {thresh} | ramp | {len(files)} run(s)")
    for f in files:
        metrics = extract_aggregated(f)
        run = os.path.basename(f).split("_stats")[0].split("run")[-1]
        if metrics and "Error" not in metrics:
            print(f"    run{run}: Reqs={metrics['Request Count']:5d}  Fails={metrics['Failure Count']:3d}"
                  f"  RPS={metrics['RPS']:5.2f}  Avg={metrics['Avg (ms)']:7.1f}  "
                  f"P50={metrics['P50 (ms)']:5d}  P95={metrics['P95 (ms)']:5d}  P99={metrics['P99 (ms)']:5d}  Max={metrics['Max (ms)']:8.1f}")
# Also add KB3 ramp as threshold 4.0
print(f"\n  Threshold 4.0 (=KB3 default) | ramp | 3 run(s) — see KB3 Ramp above")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
