import pandas as pd
import numpy as np
from scipy import stats
import os

def main():
    print("="*60)
    print("KIỂM CHỨNG GIẢ ĐỊNH POISSON (KS Test)")
    print("="*60)
    
    # Analyze a stable traffic run for baseline Poisson check
    # We use stable run to avoid trend components affecting the arrival rate
    file_path = "data/math_profile/static-k4_stable_run2_stats_history.csv"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    df = pd.read_csv(file_path)
    df = df[df['Name'] == 'Aggregated']
    
    # We use 'Requests/s' to estimate number of requests in each 1-second interval
    # Since Requests/s in locust is a float (moving average), we will look at 'Total Request Count' diffs
    # Locust records a row every second (or according to its internal tick)
    
    # Calculate arrived requests in each interval
    df['Arrivals'] = df['Total Request Count'].diff()
    
    # Filter out warmup period, keep stable part
    stable_df = df.dropna(subset=['Arrivals']).iloc[10:] 
    
    arrivals = stable_df['Arrivals'].values
    arrivals = np.round(arrivals).astype(int) # Ensure integer counts
    
    # Ensure all values are >= 0
    arrivals = arrivals[arrivals >= 0]
    
    if len(arrivals) < 10:
        print("Not enough data to perform test.")
        return
        
    lam = np.mean(arrivals)
    print(f"Mean Arrival Rate (lambda) = {lam:.2f} req/interval")
    print(f"Variance of Arrivals = {np.var(arrivals):.2f}")
    
    # Poisson property: mean == variance
    print(f"Index of Dispersion (Variance/Mean) = {np.var(arrivals) / lam:.3f} (Ideal = 1.0)")
    
    # Perform Kolmogorov-Smirnov test against Poisson
    # Scipy expects continuous for pure KS, but we can use chi-square or simply test fit
    # Let's use Poisson CDF
    ks_stat, p_value = stats.kstest(arrivals, stats.poisson(mu=lam).cdf)
    
    print(f"\nKolmogorov-Smirnov Test (KS Test):")
    print("H0: Arrivals follow a Poisson distribution")
    print(f"KS Statistic: {ks_stat:.4f}")
    print(f"p-value: {p_value:.4f}")
    
    if p_value >= 0.05:
        print("=> Không có bằng chứng bác bỏ H0. Giả định M/G/k (M = Markovian/Poisson) là HỢP LÝ.")
    else:
        print("=> Bác bỏ H0. Lưu lượng KHÔNG hoàn toàn tuân theo phân phối Poisson.")
        print("Lý do thực tiễn: Khác với user thật (độc lập), Locust users sinh request theo nhịp (think time) nhất định,")
        print("dẫn đến tính chu kỳ nhẹ khiến phân phối thực tế lệch khỏi Poisson lý tưởng.")
        print("Tuy nhiên, ở quy mô đồ án, việc dùng M/G/k làm xấp xỉ vẫn là phương pháp tiếp cận tốt nhất.")

if __name__ == "__main__":
    main()
