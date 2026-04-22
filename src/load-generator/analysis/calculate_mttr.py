import pandas as pd
import glob
import os

def calculate_mttr(pattern, slo=2000):
    files = glob.glob(pattern)
    if not files: return None
    mttrs = []
    
    for f in files:
        df = pd.read_csv(f)
        # Assuming timestamps are sequential or we can count rows (each row is ~1 or ~10 secs? history is usually per second or per 10s depending on locust)
        # Let's count rows where P95 > SLO
        # Wait, history has 'Timestamp' column in seconds
        if '95%' not in df.columns or 'Timestamp' not in df.columns:
            continue
        
        # We only care about the time period during and after the spike
        df = df[df['Name'] == 'Aggregated']
        
        # Find continuous period where latency > slo
        over_slo = df['95%'] > slo
        
        # If it never goes over SLO, mttr = 0
        if not over_slo.any():
            mttrs.append(0)
            continue
        
        # The spike is a sudden rise. We find the FIRST time it goes above SLO
        start_idx = over_slo.idxmax()
        start_time = df.loc[start_idx, 'Timestamp']
        
        # We find the LAST time it goes above SLO (or the first time it goes BELOW SLO *after* the spike)
        # Let's just find the last timestamp it was above SLO
        # This is a bit rough if it fluctuates, but good enough for MTTR estimation
        # Actually, let's find the first time it drops below SLO *after* start_idx
        post_spike = df.loc[start_idx:]
        recovered = post_spike[post_spike['95%'] <= slo]
        
        if recovered.empty:
            # Never recovered within the test
            end_time = df.iloc[-1]['Timestamp']
        else:
            end_time = recovered.iloc[0]['Timestamp']
            
        mttr = end_time - start_time
        mttrs.append(mttr)
    
    if mttrs:
        return sum(mttrs) / len(mttrs)
    return None

def main():
    print("="*60)
    print("MEAN TIME TO RECOVERY (MTTR) ANALYSIS")
    print("SLO Threshold = 2000ms")
    print("="*60)
    
    patterns = {
        'Static K=4': 'data/math_profile/static-k4_spike_recovery_run*_stats_history.csv',
        'Reactive HPA': 'data/kb2_reactive/hpa/reactive-hpa_spike_recovery_run*_stats_history.csv',
        'Proactive AI': 'data/kb3_proactive/proactive-keda_spike_recovery_run*_stats_history.csv',
    }
    
    for name, p in patterns.items():
        val = calculate_mttr(p, slo=2000)
        if val is not None:
            print(f"{name:15s}: MTTR = {val:.1f} giây")
        else:
            print(f"{name:15s}: No data")

if __name__ == "__main__":
    main()
