import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_and_plot():
    k_levels = [2, 4, 8]
    strategies = [f'static-k{k}' for k in k_levels]
    
    # 1. P99 Latency Plot
    plt.figure(figsize=(12, 6))
    
    for strategy in strategies:
        k = strategy.split('-k')[1]
        csv_file = f'data/kb1_static/k{k}/{strategy}_ramp_run1_timestamps.csv'
        if not os.path.exists(csv_file):
            continue
            
        df = pd.read_csv(csv_file)
        df['epoch_s'] = df['epoch_s'].astype(float)
        df['second'] = (df['epoch_s'] - df['epoch_s'].min()).astype(int)
        
        # Calculate P99 per second
        grouped = df.groupby('second')
        p99 = grouped['response_time_ms'].quantile(0.99)
        
        # Smooth with rolling average of 10s to remove noise
        p99_smooth = p99.rolling(window=10, min_periods=1).mean()
        
        plt.plot(p99_smooth.index, p99_smooth.values, label=f'K={k} Pods')

    plt.title('Baseline Evaluation (Ramp Profile): P99 Latency vs Load Increase')
    plt.xlabel('Time (seconds)')
    plt.ylabel('P99 Latency (ms) - 10s Smoothed')
    plt.axhline(y=200, color='r', linestyle='--', label='SLO Constraint (200ms)')
    plt.ylim(0, max(p99_smooth.max()+1000, 5000)) # Limit to 5000ms max to avoid spikes hiding details
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('notebooks/kb1_ramp_p99.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Throughput Plot
    plt.figure(figsize=(12, 6))
    for strategy in strategies:
        k = strategy.split('-k')[1]
        csv_file = f'data/kb1_static/k{k}/{strategy}_ramp_run1_timestamps.csv'
        if not os.path.exists(csv_file):
            continue
            
        df = pd.read_csv(csv_file)
        df['epoch_s'] = df['epoch_s'].astype(float)
        df['second'] = (df['epoch_s'] - df['epoch_s'].min()).astype(int)
        
        # Count successful requests per second
        tps = df[df['success'] == 1].groupby('second')['success'].count()
        tps_smooth = tps.rolling(window=10, min_periods=1).mean()
        
        plt.plot(tps_smooth.index, tps_smooth.values, label=f'K={k} Pods')

    # Theoretical maximums based on K * calibration_lambda (approx 4 req/s/pod)
    plt.title('Baseline Evaluation (Ramp Profile): Satisfied Throughput')
    plt.xlabel('Time (seconds) - Load linearly increases')
    plt.ylabel('Throughput (Requests/sec) - 10s Smoothed')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('notebooks/kb1_ramp_tps.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("PNG Graphs successfully generated!")

if __name__ == '__main__':
    analyze_and_plot()
