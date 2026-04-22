#!/usr/bin/env python3
import argparse
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def get_overall_metrics(files, name_filter="Aggregated"):
    metrics = {"rps": [], "p95": [], "p99": [], "fails": []}
    for str_f in files:
        stats_file = str_f.replace("_stats_history.csv", "_stats.csv")
        try:
            df = pd.read_csv(stats_file)
            row = df[df["Name"] == name_filter]
            if not row.empty:
                metrics["rps"].append(float(row.iloc[0]["Requests/s"]))
                metrics["p95"].append(float(row.iloc[0]["95%"]))
                metrics["p99"].append(float(row.iloc[0]["99%"]))
                metrics["fails"].append(float(row.iloc[0]["Failures/s"]))
        except Exception:
            pass
    if metrics["rps"]:
        return {k: sum(v) / len(v) for k, v in metrics.items()}
    return None

def process_csv(csv_path, name_filter="Aggregated"):
    """Loads a single Locust history CSV and returns normalized DataFrame."""
    try:
        df = pd.read_csv(csv_path)
        df = df[df["Name"] == name_filter].copy()
        if df.empty:
            return None
        
        # Normalize time
        ts = pd.to_numeric(df["Timestamp"], errors="coerce")
        df["elapsed_s"] = (ts - ts.min()).round(0).astype(int)
        
        # Ensure numeric
        cols = ["User Count", "Requests/s", "Failures/s", "50%", "95%", "99%"]
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
        # For User Count, RPS and Fails/s, 0 is the correct fill value if missing.
        for col in ["User Count", "Requests/s", "Failures/s"]:
            if col in df.columns:
                df[col] = df[col].fillna(0)
        
        # For Latency (50%, 95%, 99%), doing fillna(0) is statistically WRONG because it
        # pulls down the cross-run average. We leave them as NaN so pandas .mean() ignores them!
        
        return df[cols + ["elapsed_s"]]
    except Exception as e:
        print(f"Error processing {csv_path}: {e}")
        return None

def plot_aggregated(glob_pattern, out_path, name_filter="Aggregated", title_suffix=""):
    files = sorted(glob.glob(glob_pattern))
    if not files:
        print(f"No files found for pattern: {glob_pattern}")
        return

    print(f"Aggregating {len(files)} files for {out_path.name}...")
    
    all_dfs = []
    for f in files:
        df = process_csv(f, name_filter)
        if df is not None:
            all_dfs.append(df)
            
    if not all_dfs:
        print("No valid data to aggregate.")
        return

    # Merge all dataframes on elapsed_s
    # We use grouping to handle potential duplicate seconds within a single run
    merged = pd.concat(all_dfs)
    
    # Group by time and calculate stats
    agg = merged.groupby("elapsed_s").agg(["mean", "min", "max"])
    
    overall_metrics = get_overall_metrics(files, name_filter)
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True, constrained_layout=True)
    time = agg.index
    
    # 1. User Count
    axes[0].plot(time, agg[("User Count", "mean")], color="#2c3e50", label="Mean Users", lw=2)
    axes[0].fill_between(time, agg[("User Count", "min")], agg[("User Count", "max")], color="#2c3e50", alpha=0.1)
    axes[0].set_ylabel("User Count")
    axes[0].set_title(f"Aggregated Performance ({len(files)} runs) {title_suffix}")

    # 2. RPS
    axes[1].plot(time, agg[("Requests/s", "mean")], color="#2980b9", label="Mean RPS", lw=1.5)
    axes[1].fill_between(time, agg[("Requests/s", "min")], agg[("Requests/s", "max")], color="#2980b9", alpha=0.2)
    axes[1].set_ylabel("Requests/s")
    if overall_metrics:
        axes[1].axhline(y=overall_metrics["rps"], color='#e67e22', linestyle='--', lw=2, alpha=0.9, label=f'Global RPS = {overall_metrics["rps"]:.2f}')
        axes[1].legend(loc="upper right")

    # 3. Latency
    axes[2].plot(time, agg[("95%", "mean")], color="#27ae60", label="Mean P95", lw=1.5)
    axes[2].fill_between(time, agg[("95%", "min")], agg[("95%", "max")], color="#27ae60", alpha=0.15)
    
    axes[2].plot(time, agg[("99%", "mean")], color="#c0392b", label="Mean P99", lw=1.5)
    axes[2].fill_between(time, agg[("99%", "min")], agg[("99%", "max")], color="#c0392b", alpha=0.1)
    axes[2].set_ylabel("Latency (ms)")
    
    if overall_metrics:
        axes[2].axhline(y=overall_metrics["p95"], color='#f39c12', linestyle='--', lw=2.5, alpha=0.9, 
                        label=f'Global P95 = {int(overall_metrics["p95"])}ms')
        axes[2].axhline(y=overall_metrics["p99"], color='#d35400', linestyle='--', lw=2.5, alpha=0.9, 
                        label=f'Global P99 = {int(overall_metrics["p99"])}ms')
                        
    axes[2].legend(loc="upper right")

    # 4. Failures
    axes[3].plot(time, agg[("Failures/s", "mean")], color="#e74c3c", label="Mean Failures", lw=1.2)
    axes[3].fill_between(time, agg[("Failures/s", "min")], agg[("Failures/s", "max")], color="#e74c3c", alpha=0.2)
    axes[3].set_ylabel("Failures/s")
    axes[3].set_xlabel("Elapsed Time (s)")
    if overall_metrics:
        axes[3].axhline(y=overall_metrics["fails"], color='#c0392b', linestyle='--', lw=1.5, alpha=0.9, label=f'Global Fails/s = {overall_metrics["fails"]:.3f}')
        axes[3].legend(loc="upper right")

    for ax in axes:
        ax.grid(True, ls="--", alpha=0.4)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved aggregated plot: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--glob", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--name", default="Aggregated")
    parser.add_argument("--title", default="")
    args = parser.parse_args()
    
    plot_aggregated(args.glob, Path(args.out), args.name, args.title)
