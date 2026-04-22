#!/usr/bin/env python3
"""Extract final metrics from ALL scenarios for cross-comparison."""
import pandas as pd
import glob, os

def get_stats(csv_pattern):
    files = sorted(glob.glob(csv_pattern))
    if not files:
        return None
    sums = []
    for f in files:
        try:
            df = pd.read_csv(f)
            agg = df[df["Name"] == "Aggregated"]
            if agg.empty:
                continue
            row = agg.iloc[0]
            # Skip files with NaN in key fields
            if pd.isna(row["Requests/s"]) or pd.isna(row["95%"]):
                continue
            sums.append({
                "rps": float(row["Requests/s"]),
                "p50": int(row["50%"]),
                "p95": int(row["95%"]),
                "p99": int(row["99%"]),
                "avg": float(row["Average Response Time"]),
                "max": float(row["Max Response Time"]),
                "reqs": int(row["Request Count"]),
                "fails": int(row["Failure Count"]),
            })
        except Exception as e:
            print(f"  Warning: {f} -> {e}")
    if not sums:
        return None
    n = len(sums)
    return {
        "rps":   round(sum(s["rps"] for s in sums) / n, 2),
        "p50":   round(sum(s["p50"] for s in sums) / n, 0),
        "p95":   round(sum(s["p95"] for s in sums) / n, 0),
        "p99":   round(sum(s["p99"] for s in sums) / n, 0),
        "avg":   round(sum(s["avg"] for s in sums) / n, 1),
        "max":   round(sum(s["max"] for s in sums) / n, 1),
        "reqs":  round(sum(s["reqs"] for s in sums) / n, 0),
        "fails": round(sum(s["fails"] for s in sums) / n, 2),
        "runs":  n,
    }

MATRIX = {
    "Static-K2": {
        "Stable":         "data/math_profile/static-k2_stable_run*_stats.csv",
        "Ramp":           "data/math_profile/static-k2_ramp_run*_stats.csv",
        "Spike Recovery": "data/math_profile/static-k2_spike_recovery_run*_stats.csv",
    },
    "Static-K4": {
        "Stable":         "data/math_profile/static-k4_stable_run*_stats.csv",
        "Ramp":           "data/math_profile/static-k4_ramp_run*_stats.csv",
        "Spike Recovery": "data/math_profile/static-k4_spike_recovery_run*_stats.csv",
    },
    "Static-K8": {
        "Stable":         "data/math_profile/static-k8_stable_run*_stats.csv",
        "Ramp":           "data/math_profile/static-k8_ramp_run*_stats.csv",
        "Spike Recovery": "data/math_profile/static-k8_spike_recovery_run*_stats.csv",
    },
    "Reactive-HPA": {
        "Stable":         "data/kb2_reactive/hpa/reactive-hpa_stable_run*_stats.csv",
        "Ramp":           "data/kb2_reactive/hpa/reactive-hpa_ramp_run*_stats.csv",
        "Spike Recovery": "data/kb2_reactive/hpa/reactive-hpa_spike_recovery_run*_stats.csv",
    },
    "Proactive-AI": {
        "Stable":         "data/kb3_proactive/proactive-keda_stable_run*_stats.csv",
        "Ramp":           "data/kb3_proactive/proactive-keda_ramp_run*_stats.csv",
        "Spike Recovery": "data/kb3_proactive/proactive-keda_spike_recovery_run*_stats.csv",
    },
}

results = []
for scenario, profiles in MATRIX.items():
    for traffic, pattern in profiles.items():
        stats = get_stats(pattern)
        if stats:
            results.append({
                "Scenario": scenario,
                "Traffic": traffic,
                "Runs": stats["runs"],
                "Avg RPS": stats["rps"],
                "Avg Latency (ms)": stats["avg"],
                "P50 (ms)": int(stats["p50"]),
                "P95 (ms)": int(stats["p95"]),
                "P99 (ms)": int(stats["p99"]),
                "Max (ms)": stats["max"],
                "Avg Reqs": int(stats["reqs"]),
                "Avg Fails": stats["fails"],
            })

df = pd.DataFrame(results)
out = "data/final_performance_comparison.csv"
df.to_csv(out, index=False)

# Print nicely
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 15)
print(f"Saved: {out}\n")
print(df.to_string(index=False))
