#!/usr/bin/env python3
"""
Vẽ nhanh từ Locust *_stats_history.csv (multi-panel, trục thời gian tương đối).

Chạy từ thư mục gốc repo _repo_clone (để đường dẫn data/... khớp các script khác):

  python src/load-generator/analysis/plot_locust_history.py ^
    --csv data/kb3_proactive/proactive-keda_ramp_run1_stats_history.csv ^
    --out phan-tich/figs/kb3_ramp_run1.png

Tuỳ chọn --name "/collect" hoặc --name Aggregated (mặc định: Aggregated).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _prep(df: pd.DataFrame, name_filter: str) -> pd.DataFrame:
    d = df[df["Name"] == name_filter].copy()
    if d.empty:
        raise ValueError(f"No rows with Name == {name_filter!r}. Check --name.")
    ts = pd.to_numeric(d["Timestamp"], errors="coerce")
    d["elapsed_s"] = ts - ts.min()
    for col in ("99%", "95%", "50%", "Requests/s", "Failures/s", "User Count"):
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce")
    return d.sort_values("elapsed_s")


def plot_history(csv_path: Path, out_path: Path, name_filter: str) -> None:
    df = _prep(pd.read_csv(csv_path), name_filter)
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True, constrained_layout=True)

    axes[0].plot(df["elapsed_s"], df["User Count"], color="#34495e", lw=1.2)
    axes[0].set_ylabel("User count")
    axes[0].set_title(f"{csv_path.name} — {name_filter}")

    axes[1].plot(df["elapsed_s"], df["Requests/s"], color="#2980b9", lw=1.2)
    axes[1].set_ylabel("Requests/s")

    if "95%" in df.columns and "99%" in df.columns:
        axes[2].plot(df["elapsed_s"], df["95%"], label="P95", color="#27ae60", lw=1.0, alpha=0.9)
        axes[2].plot(df["elapsed_s"], df["99%"], label="P99", color="#c0392b", lw=1.0, alpha=0.9)
        axes[2].set_ylabel("Latency (ms)")
        axes[2].legend(loc="upper right", fontsize=8)

    if "Failures/s" in df.columns:
        axes[3].fill_between(df["elapsed_s"], df["Failures/s"], color="#e74c3c", alpha=0.35)
        axes[3].plot(df["elapsed_s"], df["Failures/s"], color="#c0392b", lw=1.0)
        axes[3].set_ylabel("Failures/s")

    axes[-1].set_xlabel("Elapsed time (s)")
    for ax in axes:
        ax.grid(True, ls="--", alpha=0.35)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_run_summaries(glob_pattern: str, out_path: Path, name_filter: str) -> None:
    import glob

    paths = sorted(glob.glob(glob_pattern))
    if not paths:
        raise FileNotFoundError(f"No files match: {glob_pattern}")

    rows = []
    for p in paths:
        s = pd.read_csv(p)
        s = s[s["Name"] == name_filter]
        if s.empty:
            continue
        row = s.iloc[0]
        rows.append(
            {
                "run": Path(p).stem,
                "p50": pd.to_numeric(row.get("50%"), errors="coerce"),
                "p95": pd.to_numeric(row.get("95%"), errors="coerce"),
                "p99": pd.to_numeric(row.get("99%"), errors="coerce"),
                "avg_ms": pd.to_numeric(row.get("Average Response Time"), errors="coerce"),
                "fail_count": pd.to_numeric(row.get("Failure Count"), errors="coerce"),
                "req_count": pd.to_numeric(row.get("Request Count"), errors="coerce"),
            }
        )
    if not rows:
        raise ValueError("No summary rows; check --name and glob.")

    d = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
    x = range(len(d))
    ax.boxplot(
        [d["p50"].dropna(), d["p95"].dropna(), d["p99"].dropna()],
        tick_labels=["P50", "P95", "P99"],
    )
    ax.set_title(f"End-of-run latency spread ({len(d)} runs) — {name_filter}")
    ax.set_ylabel("ms")
    ax.grid(True, axis="y", ls="--", alpha=0.35)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot Locust CSV exports.")
    ap.add_argument("--csv", type=Path, help="Path to *_stats_history.csv")
    ap.add_argument("--out", type=Path, required=True, help="Output PNG path")
    ap.add_argument("--name", default="Aggregated", help='Locust Name filter (default "Aggregated")')
    ap.add_argument(
        "--summary-glob",
        metavar="PATTERN",
        help="Instead of time series: glob of *_stats.csv for simple P50/P95/P99 box view",
    )
    args = ap.parse_args()

    if args.summary_glob:
        plot_run_summaries(args.summary_glob, args.out, args.name)
    else:
        if not args.csv:
            ap.error("--csv is required unless --summary-glob is set")
        plot_history(args.csv, args.out, args.name)

    print(f"Saved: {args.out.resolve()}")


if __name__ == "__main__":
    main()
