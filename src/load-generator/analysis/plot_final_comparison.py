#!/usr/bin/env python3
"""Final cross-scenario comparison charts for the project report."""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def main():
    df = pd.read_csv("data/final_performance_comparison.csv")
    out_dir = "results/figs"
    os.makedirs(out_dir, exist_ok=True)

    scenarios = ["Static-K2", "Static-K4", "Static-K8", "Reactive-HPA", "Proactive-AI"]
    traffics = ["Stable", "Ramp", "Spike Recovery"]
    colors = {
        "Static-K2":    "#95a5a6",
        "Static-K4":    "#7f8c8d",
        "Static-K8":    "#566573",
        "Reactive-HPA": "#e74c3c",
        "Proactive-AI": "#2ecc71",
    }

    # ── Chart 1: Grouped Bar — P95 Latency per Traffic ──────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.suptitle("P95 Latency Comparison Across Scaling Strategies", fontsize=16, fontweight='bold', y=1.02)

    for idx, traffic in enumerate(traffics):
        ax = axes[idx]
        sub = df[df["Traffic"] == traffic]
        vals, cols, labels = [], [], []
        for s in scenarios:
            row = sub[sub["Scenario"] == s]
            if not row.empty:
                vals.append(row["P95 (ms)"].values[0])
                cols.append(colors[s])
                labels.append(s)

        bars = ax.bar(range(len(vals)), vals, color=cols, edgecolor='black', linewidth=0.8, alpha=0.85)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
        ax.set_title(f"Traffic: {traffic}", fontsize=13, fontweight='bold')
        ax.set_ylabel("P95 Latency (ms)" if idx == 0 else "")
        ax.grid(axis='y', linestyle='--', alpha=0.4)

        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, v + max(vals)*0.02,
                    f"{int(v)}", ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.tight_layout()
    p = os.path.join(out_dir, "cross_p95_by_traffic.png")
    plt.savefig(p, dpi=300, bbox_inches='tight')
    print(f"Saved: {p}")
    plt.close()

    # ── Chart 2: Grouped Bar — Avg RPS per Traffic ──────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    fig.suptitle("Throughput (RPS) Comparison Across Scaling Strategies", fontsize=16, fontweight='bold', y=1.02)

    for idx, traffic in enumerate(traffics):
        ax = axes[idx]
        sub = df[df["Traffic"] == traffic]
        vals, cols, labels = [], [], []
        for s in scenarios:
            row = sub[sub["Scenario"] == s]
            if not row.empty:
                vals.append(row["Avg RPS"].values[0])
                cols.append(colors[s])
                labels.append(s)

        bars = ax.bar(range(len(vals)), vals, color=cols, edgecolor='black', linewidth=0.8, alpha=0.85)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
        ax.set_title(f"Traffic: {traffic}", fontsize=13, fontweight='bold')
        ax.set_ylabel("Avg RPS" if idx == 0 else "")
        ax.grid(axis='y', linestyle='--', alpha=0.4)

        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, v + max(vals)*0.02,
                    f"{v:.2f}", ha='center', va='bottom', fontsize=8, fontweight='bold')

    plt.tight_layout()
    p = os.path.join(out_dir, "cross_rps_by_traffic.png")
    plt.savefig(p, dpi=300, bbox_inches='tight')
    print(f"Saved: {p}")
    plt.close()

    # ── Chart 3: Heatmap-style table — P95 Matrix ───────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_axis_off()
    ax.set_title("Performance Matrix: Avg P95 Latency (ms)", fontsize=14, fontweight='bold', pad=20)

    cell_data = []
    for s in scenarios:
        row = []
        for t in traffics:
            val = df[(df["Scenario"] == s) & (df["Traffic"] == t)]["P95 (ms)"]
            row.append(f"{int(val.values[0])}" if not val.empty else "N/A")
        cell_data.append(row)

    table = ax.table(cellText=cell_data, rowLabels=scenarios, colLabels=traffics,
                     cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)

    # Color cells by value
    for (i, j), cell in table.get_celld().items():
        if i == 0:  # header
            cell.set_facecolor('#34495e')
            cell.set_text_props(color='white', fontweight='bold')
        elif j == -1:  # row labels
            cell.set_facecolor('#ecf0f1')
            cell.set_text_props(fontweight='bold')
        else:
            try:
                val = int(cell.get_text().get_text())
                # Green (low) to Red (high)
                norm = min(val / 12000, 1.0)
                r = min(norm * 2, 1.0)
                g = min((1 - norm) * 2, 1.0)
                cell.set_facecolor((r, g, 0.3, 0.3))
            except:
                pass

    plt.tight_layout()
    p = os.path.join(out_dir, "cross_p95_heatmap.png")
    plt.savefig(p, dpi=300, bbox_inches='tight')
    print(f"Saved: {p}")
    plt.close()

    print("\nAll cross-scenario charts generated successfully!")

if __name__ == "__main__":
    main()
