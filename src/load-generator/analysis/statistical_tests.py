import numpy as np
from scipy import stats

def main():
    print("="*60)
    print("KIỂM ĐỊNH THỐNG KÊ (ANOVA / KRUSKAL-WALLIS)")
    print("Kịch bản: Spike Recovery (P95 Latency)")
    print("="*60)

    # Data (P95 Latency from 3 runs)
    k4 = [1400, 1400, 1200]
    hpa = [9100, 11000, 8800]
    ai = [6600, 7200, 5600]

    all_data = k4 + hpa + ai

    # 1. Normality Test (Shapiro-Wilk)
    print("\n1. Kiểm định phân phối chuẩn (Shapiro-Wilk Test)")
    print("H0: Dữ liệu tuân theo phân phối chuẩn")
    
    # Normally, Shapiro-Wilk needs n >= 3. With n=3 it's very weakly powered, but we do it anyway.
    _, p_k4 = stats.shapiro(k4)
    _, p_hpa = stats.shapiro(hpa)
    _, p_ai = stats.shapiro(ai)
    
    print(f" - Static K=4 : p-value = {p_k4:.4f}")
    print(f" - Reactive HPA: p-value = {p_hpa:.4f}")
    print(f" - Proactive AI: p-value = {p_ai:.4f}")

    is_normal = (p_k4 >= 0.05) and (p_hpa >= 0.05) and (p_ai >= 0.05)
    if is_normal:
        print(" => Không có bằng chứng bác bỏ H0. Giả định phân phối chuẩn thỏa mãn (p >= 0.05).")
    else:
        print(" => Dữ liệu KHÔNG tuân theo phân phối chuẩn (p < 0.05).")

    # 2. Homogeneity of Variances Test (Levene)
    print("\n2. Kiểm định phương sai đồng nhất (Levene Test)")
    print("H0: Phương sai của các nhóm là bằng nhau")
    w, p_levene = stats.levene(k4, hpa, ai)
    print(f" - Levene W = {w:.4f}, p-value = {p_levene:.4f}")
    
    is_homogenous = (p_levene >= 0.05)
    if is_homogenous:
        print(" => Không có bằng chứng bác bỏ H0. Giả định phương sai đồng nhất thỏa mãn.")
    else:
        print(" => Phương sai các nhóm KHÔNG đồng nhất.")

    # 3. Main Test
    print("\n3. Kiểm chứng giả thuyết chính")
    if is_normal and is_homogenous:
        print(" => Sử dụng One-way ANOVA")
        f_stat, p_main = stats.f_oneway(k4, hpa, ai)
        print(f" - ANOVA F-statistic = {f_stat:.4f}, p-value = {p_main:.4f}")
    else:
        print(" => Sử dụng Kruskal-Wallis (Non-parametric) do vi phạm giả định ANOVA")
        h_stat, p_main = stats.kruskal(k4, hpa, ai)
        print(f" - Kruskal-Wallis H-statistic = {h_stat:.4f}, p-value = {p_main:.4f}")

    if p_main < 0.05:
        print(" => Có sự khác biệt CÓ Ý NGHĨA THỐNG KÊ (p < 0.05) về P95 Latency giữa các chiến lược.")
        
        # 4. Effect Size (Cohen's d) AI vs HPA
        print("\n4. Tính Effect Size (Cohen's d): Proactive AI vs Reactive HPA")
        mean_ai, std_ai = np.mean(ai), np.std(ai, ddof=1)
        mean_hpa, std_hpa = np.mean(hpa), np.std(hpa, ddof=1)
        
        pooled_std = np.sqrt(((len(ai)-1)*std_ai**2 + (len(hpa)-1)*std_hpa**2) / (len(ai) + len(hpa) - 2))
        d = abs(mean_ai - mean_hpa) / pooled_std
        print(f" - Cohen's d = {d:.4f}")
        if d >= 0.8:
            print(" => Effect size: LARGE (Sự khác biệt cực kỳ rõ ràng và có ý nghĩa thực tiễn lớn).")
    else:
        print(" => Không có sự khác biệt có ý nghĩa thống kê giữa các chiến lược.")

if __name__ == "__main__":
    main()
