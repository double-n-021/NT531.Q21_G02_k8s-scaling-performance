import pandas as pd
import matplotlib.pyplot as plt
import os

# --- CONFIG ---
INPUT_FILE = "data/kb4_sensitivity/comparison_summary.csv"
OUTPUT_PLOT = "data/kb4_sensitivity/kb4_performance_dashboard.png"

# Windowing configuration (in seconds)
TIME_WINDOW = 600 

def create_dashboard():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run sensitivity_comparison.py first.")
        return

    df = pd.read_csv(INPUT_FILE)
    
    if TIME_WINDOW:
        df = df[df['time'] <= TIME_WINDOW]

    # Map colors to thresholds
    colors = {
        "2.0 (Aggressive)": "#2ecc71", # Green
        "4.0 (Balanced)":   "#e67e22", # Orange
        "6.0 (Conservative)": "#3498db"  # Blue
    }
    
    # Global metrics from Locust _stats.csv (Aggregated row, averaged across runs)
    # These are the GROUND TRUTH numbers that match final_performance_comparison.csv
    GLOBAL_METRICS = {
        "2.0 (Aggressive)": {"rps": 5.90, "p95": 8150, "p99": 12500},
        "4.0 (Balanced)":   {"rps": 4.85, "p95": 8767, "p99": 22667},
        "6.0 (Conservative)": {"rps": 5.77, "p95": 8200, "p99": 17000},
    }

    # Create Subplots (3 rows, 1 col)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 16), sharex=True)
    plt.subplots_adjust(hspace=0.25)

    thresholds = df['threshold'].unique()

    # --- PANEL 1: Load vs Throughput ---
    # Background for User Count
    ref_df = df[df['threshold'] == thresholds[0]]
    ax1.fill_between(ref_df['time'], ref_df['users'], color='#bdc3c7', alpha=0.2, label='User Count (Load)')
    
    for label in thresholds:
        subset = df[df['threshold'] == label]
        ax1.plot(subset['time'], subset['rps'], label=f"RPS ({label})", color=colors.get(label), linewidth=2)
    
    ax1.set_title("PANEL 1: System Load vs Throughput (RPS)", fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel("Quantity", fontsize=12)
    for label in thresholds:
        if label in GLOBAL_METRICS:
            avg_rps = GLOBAL_METRICS[label]["rps"]
            ax1.axhline(y=avg_rps, color=colors.get(label), linestyle='--', lw=1.5, alpha=0.6,
                        label=f'Global RPS ({label.split(" ")[0]}) = {avg_rps:.2f}')
    ax1.legend(loc='upper left', frameon=True, fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- PANEL 2: Latency Spectrum (P95) ---
    for label in thresholds:
        subset = df[df['threshold'] == label]
        ax2.plot(subset['time'], subset['p95'], label=label, color=colors.get(label), linewidth=2.5)
    
    ax2.set_title("PANEL 2: Response Time Sensitivity (P95 Latency)", fontsize=14, fontweight='bold', pad=15)
    ax2.set_ylabel("Latency (ms)", fontsize=12)
    for label in thresholds:
        if label in GLOBAL_METRICS:
            avg_p95 = GLOBAL_METRICS[label]["p95"]
            ax2.axhline(y=avg_p95, color=colors.get(label), linestyle='--', lw=1.5, alpha=0.6,
                        label=f'Global P95 ({label.split(" ")[0]}) = {int(avg_p95)}ms')
    ax2.legend(loc='upper left', frameon=True, fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.6)

    # --- PANEL 3: Peak Stability (P99) ---
    for label in thresholds:
        subset = df[df['threshold'] == label]
        ax3.plot(subset['time'], subset['p99'], label=label, color=colors.get(label), linewidth=1.5, alpha=0.8)
    
    ax3.set_title("PANEL 3: System Stability & Peak Jitter (P99 Latency)", fontsize=14, fontweight='bold', pad=15)
    ax3.set_ylabel("Latency (ms)", fontsize=12)
    ax3.set_xlabel("Elapsed Time (Seconds)", fontsize=12)
    for label in thresholds:
        if label in GLOBAL_METRICS:
            avg_p99 = GLOBAL_METRICS[label]["p99"]
            ax3.axhline(y=avg_p99, color=colors.get(label), linestyle='--', lw=1.5, alpha=0.6,
                        label=f'Global P99 ({label.split(" ")[0]}) = {int(avg_p99)}ms')
    ax3.legend(loc='upper left', frameon=True, fontsize=9)
    ax3.grid(True, linestyle='--', alpha=0.6)

    # Global formatting
    plt.suptitle("KB4: Proactive Scaling Sensitivity Dashboard", fontsize=18, fontweight='bold', y=0.96)
    
    # Save output
    plt.savefig(OUTPUT_PLOT, dpi=300, bbox_inches='tight')
    print(f"\nDashboard generated successfully: {OUTPUT_PLOT}")

if __name__ == "__main__":
    create_dashboard()
