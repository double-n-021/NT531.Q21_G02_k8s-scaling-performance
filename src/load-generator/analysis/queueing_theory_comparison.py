#!/usr/bin/env python3
"""
So sánh Lý thuyết Hàng đợi M/G/k (Kimura 1983) vs Thực nghiệm.
Trả lời câu hỏi nghiên cứu Q2 trong đề cương.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import factorial, exp
import os

# ── Parameters from calibration data ──────────────────────────────
# From KB0 calibration: processing_duration ~600ms (CPU-bound math)
# mu = 1/mean_service_time
SERVICE_TIME_MS = 600  # mean processing time (ms) from calibration
MU = 1000 / SERVICE_TIME_MS  # service rate per pod (req/s) ≈ 1.67
CS = 0.3  # coefficient of variation of service time (estimated from data)

def erlang_c(k, A):
    """Compute Erlang-C: probability of queuing in M/M/k."""
    rho = A / k
    if rho >= 1:
        return 1.0  # System overloaded
    
    # Numerator: A^k / (k! * (1-rho))
    numerator = (A ** k) / (factorial(k) * (1 - rho))
    
    # Denominator: sum(A^n/n!, n=0..k-1) + numerator
    sum_terms = sum((A ** n) / factorial(n) for n in range(k))
    denominator = sum_terms + numerator
    
    return numerator / denominator

def mgk_latency(lam, k, mu, Cs):
    """
    Kimura (1983) M/G/k approximation.
    Returns expected total response time E[T] in ms.
    """
    A = lam / mu  # offered load (Erlang)
    rho = A / k   # utilization per server
    
    if rho >= 0.99:
        return float('inf')
    
    # Step 1: Erlang-C
    Ck = erlang_c(k, A)
    
    # Step 2: E[Wq] for M/M/k
    Wq_mmk = Ck / (k * mu * (1 - rho))
    
    # Step 3: Kimura correction for M/G/k
    Wq_mgk = Wq_mmk * (Cs**2 + 1) / 2
    
    # Step 4: Total response time E[T] = Wq + 1/mu
    ET = Wq_mgk + (1 / mu)
    
    return ET * 1000  # convert to ms

def main():
    out_dir = "results/figs/cross_comparison"
    os.makedirs(out_dir, exist_ok=True)
    
    # ── Theoretical curves for different k ──────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # --- Panel 1: Latency vs Utilization (rho) ---
    ax1 = axes[0]
    for k in [2, 4, 8]:
        rhos = np.linspace(0.05, 0.95, 100)
        lambdas = rhos * k * MU
        latencies = [mgk_latency(l, k, MU, CS) for l in lambdas]
        ax1.plot(rhos, latencies, linewidth=2, label=f'M/G/{k} (Kimura)')
    
    # Overlay actual data points from experiments
    # Use the actual measured data from extract_final_metrics
    actual_data = {
        # (label, rho_estimated, avg_latency_ms, marker, color)
        'Static K=2 Stable': (0.35, 687, 's', '#95a5a6'),
        'Static K=4 Stable': (0.24, 352, 's', '#7f8c8d'),
        'Static K=4 Ramp': (0.72, 690, '^', '#7f8c8d'),
        'Static K=8 Stable': (0.15, 1001, 's', '#566573'),
        'HPA Stable': (0.31, 917, 'o', '#e74c3c'),
        'HPA Ramp': (0.68, 2006, '^', '#e74c3c'),
        'AI Stable': (0.30, 1035, 'D', '#2ecc71'),
        'AI Ramp': (0.60, 2140, '^', '#2ecc71'),
    }
    
    for label, (rho, lat, marker, color) in actual_data.items():
        ax1.scatter(rho, lat, marker=marker, s=120, c=color, edgecolors='black',
                   linewidths=1.2, zorder=5, label=f'{label} (measured)')
    
    ax1.set_xlabel('Utilization (ρ)', fontsize=12)
    ax1.set_ylabel('Response Time (ms)', fontsize=12)
    ax1.set_title('M/G/k Theory vs Measured Latency', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 3000)
    ax1.axhline(y=500, color='red', linestyle='--', alpha=0.5, label='SLO = 500ms')
    ax1.legend(fontsize=7, loc='upper left', ncol=2)
    ax1.grid(True, alpha=0.3)
    
    # --- Panel 2: Latency vs Lambda (arrival rate) with k=4 ---
    ax2 = axes[1]
    k = 4
    lambdas_theory = np.linspace(0.5, k * MU * 0.95, 100)
    latencies_theory = [mgk_latency(l, k, MU, CS) for l in lambdas_theory]
    ax2.plot(lambdas_theory, latencies_theory, 'b-', linewidth=2.5,
             label=f'Kimura M/G/{k} (μ={MU:.2f}, Cs={CS})')
    
    # Actual data points for k=4 static
    measured_points = [
        # (lambda, latency, label)
        (1.62, 352, 'K4 Stable'),
        (7.35, 690, 'K4 Ramp'),
        (3.02, 529, 'K4 Spike Recovery'),
    ]
    for lam, lat, lbl in measured_points:
        ax2.scatter(lam, lat, s=150, c='orange', edgecolors='black', 
                   linewidths=1.5, zorder=5, marker='o')
        ax2.annotate(lbl, (lam, lat), textcoords="offset points", 
                    xytext=(10, 10), fontsize=9, fontweight='bold')
    
    ax2.set_xlabel('Arrival Rate λ (req/s)', fontsize=12)
    ax2.set_ylabel('Response Time (ms)', fontsize=12)
    ax2.set_title(f'Theory vs Experiment (Static K={k})', fontsize=14, fontweight='bold')
    ax2.axhline(y=500, color='red', linestyle='--', alpha=0.5, label='SLO = 500ms')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(out_dir, "queueing_theory_vs_experiment.png")
    plt.savefig(path, dpi=300, bbox_inches='tight')
    print(f"Saved: {path}")
    plt.close()
    
    # ── Print theoretical predictions ──────────────────────────
    print("\n" + "="*70)
    print("QUEUEING THEORY PREDICTIONS vs MEASURED DATA")
    print("="*70)
    print(f"Parameters: μ = {MU:.2f} req/s, Cs = {CS}, Service Time = {SERVICE_TIME_MS}ms")
    print()
    
    configs = [
        ("Static K=2, Stable", 2, 0.59, 687),
        ("Static K=2, Ramp", 2, 1.61, 3389),
        ("Static K=4, Stable", 4, 1.62, 352),
        ("Static K=4, Ramp", 4, 7.35, 690),
        ("Static K=4, Spike Recovery", 4, 3.02, 529),
        ("Static K=8, Stable", 8, 1.98, 1001),
        ("Static K=8, Ramp", 8, 8.50, 1124),
    ]
    
    print(f"{'Config':<30s} {'k':>3s} {'λ':>6s} {'ρ':>6s} {'Theory(ms)':>11s} {'Measured(ms)':>13s} {'Δ%':>8s}")
    print("-" * 80)
    for name, k, lam, measured in configs:
        rho = lam / (k * MU)
        theory = mgk_latency(lam, k, MU, CS)
        if theory < 1e6:
            delta = ((measured - theory) / theory) * 100
            print(f"{name:<30s} {k:>3d} {lam:>6.2f} {rho:>6.2f} {theory:>11.1f} {measured:>13.1f} {delta:>+7.1f}%")
        else:
            print(f"{name:<30s} {k:>3d} {lam:>6.2f} {rho:>6.2f} {'OVERLOAD':>11s} {measured:>13.1f}")

if __name__ == "__main__":
    main()
