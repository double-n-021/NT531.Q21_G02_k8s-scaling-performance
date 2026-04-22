import pandas as pd
import glob
import os
import numpy as np

# --- CONFIG ---
DATA_PATHS = {
    "2.0 (Aggressive)": "data/kb4_sensitivity/threshold_2.0/proactive-keda_ramp_run*_stats_history.csv",
    "4.0 (Balanced)":   "data/kb3_proactive/proactive-keda_ramp_run*_stats_history.csv",
    "6.0 (Conservative)": "data/kb4_sensitivity/threshold_6.0/proactive-keda_ramp_run*_stats_history.csv"
}

OUTPUT_SUMMARY = "data/kb4_sensitivity/comparison_summary.csv"

def process_threshold(label, path_pattern):
    files = glob.glob(path_pattern)
    print(f"Processing {label}: found {len(files)} runs.")
    
    all_runs = []
    for i, f in enumerate(files):
        try:
            df = pd.read_csv(f)
            # Basic cleanup
            df = df[df['Name'] == 'Aggregated'].copy()
            
            # Normalize time to start at 0
            df['elapsed'] = df['Timestamp'] - df['Timestamp'].min()
            
            # Select relevant columns
            # Locust columns can have different names depending on version
            cols = {
                'elapsed': 'time',
                'User Count': 'users',
                'Requests/s': 'rps',
                '95%': 'p95',
                '99%': 'p99',
                'Total Average Response Time': 'avg_lat'
            }
            # Handle potential N/A in latency
            for col in ['95%', '99%', 'Total Average Response Time']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df_clean = df.rename(columns=cols)[list(cols.values())]
            df_clean['run'] = i + 1
            all_runs.append(df_clean)
        except Exception as e:
            print(f"  Error reading {f}: {e}")

    if not all_runs:
        return None

    # Merge all runs
    combined = pd.concat(all_runs)
    
    # Group by elapsed time to get average across runs
    summary = combined.groupby('time').agg({
        'users': 'mean',
        'rps': 'mean',
        'p95': 'mean',
        'p99': 'mean',
        'avg_lat': 'mean'
    }).reset_index()
    
    summary['threshold'] = label
    return summary

def run_analysis():
    results = []
    for label, pattern in DATA_PATHS.items():
        # Adjust pattern for local execution (assuming run from project root)
        sum_df = process_threshold(label, pattern)
        if sum_df is not None:
            results.append(sum_df)

    if not results:
        print("No data found to analyze!")
        return

    final_df = pd.concat(results)
    
    # Calculate global metrics for the report
    print("\n" + "="*50)
    print("SENSITIVITY ANALYSIS SUMMARY")
    print("="*50)
    
    report_data = []
    
    for label in DATA_PATHS.keys():
        threshold_data = final_df[final_df['threshold'] == label]
        if threshold_data.empty: continue
        
        # We focus on the "High Load" phase (users > 10)
        high_load = threshold_data[threshold_data['users'] > 10]
        
        avg_p95 = high_load['p95'].mean()
        max_p99 = high_load['p99'].max()
        avg_rps = high_load['rps'].mean()
        
        print(f"\nThreshold: {label}")
        print(f"  - Avg P95 Latency (High Load): {avg_p95:.2f} ms")
        print(f"  - Max P99 Latency:             {max_p99:.2f} ms")
        print(f"  - Avg Throughput:              {avg_rps:.2f} RPS")
        
        report_data.append({
            "Threshold": label,
            "Avg P95 (ms)": round(avg_p95, 2),
            "Max P99 (ms)": round(max_p99, 2),
            "Avg RPS": round(avg_rps, 2)
        })

    # Save for later use in charts
    final_df.to_csv(OUTPUT_SUMMARY, index=False)
    print(f"\nDetailed comparison saved to: {OUTPUT_SUMMARY}")

    # --- PLOTTING ---
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        
        thresholds = final_df['threshold'].unique()
        colors = ['#2ecc71', '#e67e22', '#3498db'] # Green, Orange, Blue
        
        for i, label in enumerate(thresholds):
            subset = final_df[final_df['threshold'] == label]
            plt.plot(subset['time'], subset['p95'], label=label, color=colors[i % len(colors)], linewidth=2)
        
        plt.title('Performance Comparison: P95 Latency by Scaling Threshold', fontsize=14)
        plt.xlabel('Elapsed Time (s)', fontsize=12)
        plt.ylabel('P95 Response Time (ms)', fontsize=12)
        plt.legend(title='Threshold')
        plt.grid(True, linestyle='--', alpha=0.6)
        
        plot_path = "data/kb4_sensitivity/latency_comparison.png"
        plt.savefig(plot_path, dpi=300)
        print(f"Chart generated and saved to: {plot_path}")
    except Exception as e:
        print(f"Could not generate plot automatically: {e}")

if __name__ == "__main__":
    run_analysis()
