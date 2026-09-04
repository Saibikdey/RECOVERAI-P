#!/usr/bin/env python3
"""
RecoverAI: 20-Seed Robustness Evaluation CLI
Evaluates RecoverAI (AI + Policy Engine) vs Baseline 1 (Blind Retry) vs Baseline 2 (Rule-Based)
across 20 pseudo-random dataset seeds to demonstrate variance, economic net revenue, and robustness.
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.orchestrator import RecoveryOrchestrator

def main():
    print("=" * 125)
    print("                                  RECOVERAI: 20-SEED ROBUSTNESS EVALUATION                                   ")
    print("=" * 125)
    print("Evaluating 20 independent seeds (100 synthetic failed payments per seed = 2,000 total transactions)...")
    print("-" * 125)

    res = RecoveryOrchestrator.run_multi_seed_evaluation(seed_start=1, seed_end=20, count_per_seed=100)

    # Per-Seed Summary Table Header
    print(f"{'Seed':<5} | {'Risk Amount':<13} | {'Blind Net':<11} | {'Blind Tx%':<9} | {'Rule Net':<11} | {'Rule Tx%':<8} | {'AI Gross':<11} | {'AI Cost':<8} | {'AI Net':<11} | {'AI Rev%':<7} | {'AI Tx%':<7} | {'Net Uplift v Rule':<17}")
    print("-" * 125)

    for item in res.per_seed_results:
        print(
            f"{item['seed']:<5} | "
            f"₹{item['total_revenue_at_risk']:>11,.0f} | "
            f"₹{item['blind_net_revenue']:>9,.0f} | "
            f"{item['blind_tx_recovery_rate']:>8.1f}% | "
            f"₹{item['rule_net_revenue']:>9,.0f} | "
            f"{item['rule_tx_recovery_rate']:>7.1f}% | "
            f"₹{item['ai_gross_revenue']:>9,.0f} | "
            f"₹{item['ai_intervention_cost']:>6,.0f} | "
            f"₹{item['ai_net_revenue']:>9,.0f} | "
            f"{item['ai_revenue_rate']:>6.1f}% | "
            f"{item['ai_tx_recovery_rate']:>6.1f}% | "
            f"+₹{item['net_uplift_over_rule']:>14,.0f}"
        )

    print("=" * 125)
    print("                                            AGGREGATE SUMMARY (20 SEEDS)                                            ")
    print("=" * 125)
    print(f"Total Datasets Evaluated           : {res.seed_count} independent seeds (2,000 transactions)")
    print()
    print("1. STRATEGY PERFORMANCE BREAKDOWN:")
    print("-" * 125)
    print(f"• RecoverAI (AI + Policy Engine)   :")
    print(f"    - Mean Gross Revenue           : ₹{res.ai_mean_gross_revenue:,.2f}")
    print(f"    - Mean Intervention Cost       : ₹{res.ai_mean_intervention_cost:,.2f}")
    print(f"    - Mean Net Revenue             : ₹{res.ai_mean_net_revenue:,.2f} (StdDev: ±₹{res.ai_std_dev_net_revenue:,.2f})")
    print(f"    - Mean Revenue Recovery Rate   : {res.ai_mean_revenue_rate:.2f}% (Gross Recovered / Revenue at Risk)")
    print(f"    - Mean Transaction Recovery    : {res.ai_mean_tx_recovery_rate:.2f}% (Range: {res.ai_min_tx_recovery_rate:.1f}% – {res.ai_max_tx_recovery_rate:.1f}%, Median: {res.ai_median_tx_recovery_rate:.1f}%, StdDev: ±{res.ai_std_dev_tx_rate:.2f}%)")
    print()
    print(f"• Simple Rule-Based Baseline       :")
    print(f"    - Mean Gross Revenue           : ₹{res.rule_mean_gross_revenue:,.2f}")
    print(f"    - Mean Intervention Cost       : ₹{res.rule_mean_intervention_cost:,.2f}")
    print(f"    - Mean Net Revenue             : ₹{res.rule_mean_net_revenue:,.2f}")
    print(f"    - Mean Revenue Recovery Rate   : {res.rule_mean_revenue_rate:.2f}%")
    print(f"    - Mean Transaction Recovery    : {res.rule_mean_tx_recovery_rate:.2f}% (StdDev: ±{res.rule_std_dev_tx_rate:.2f}%)")
    print()
    print(f"• Naive Blind Retry Baseline       :")
    print(f"    - Mean Gross Revenue           : ₹{res.blind_mean_gross_revenue:,.2f}")
    print(f"    - Mean Intervention Cost       : ₹{res.blind_mean_intervention_cost:,.2f}")
    print(f"    - Mean Net Revenue             : ₹{res.blind_mean_net_revenue:,.2f}")
    print(f"    - Mean Revenue Recovery Rate   : {res.blind_mean_revenue_rate:.2f}%")
    print(f"    - Mean Transaction Recovery    : {res.blind_mean_tx_recovery_rate:.2f}% (StdDev: ±{res.blind_std_dev_tx_rate:.2f}%)")
    print("-" * 125)
    print()
    print("2. ECONOMIC NET REVENUE UPLIFT:")
    print("-" * 125)
    print(f"• Net Uplift vs Simple Rule Baseline : +₹{res.mean_net_uplift_over_rule:,.2f} (+{res.net_revenue_uplift_pct_over_rule:.2f}% net revenue uplift)")
    print(f"• Net Uplift vs Blind Retry Baseline : +₹{res.mean_net_uplift_over_blind:,.2f} (+{res.net_revenue_uplift_pct_over_blind:.2f}% net revenue uplift)")
    print("-" * 125)
    print()
    print("3. TRANSACTION RECOVERY ADVANTAGE:")
    print("-" * 125)
    print(f"• Transaction Recovery Advantage vs Rule  : +{res.tx_advantage_over_rule_pts:.2f} percentage points")
    print(f"• Transaction Recovery Advantage vs Blind : +{res.tx_advantage_over_blind_pts:.2f} percentage points")
    print("=" * 125)
    print("* All figures derived from documented synthetic domain simulation assumptions.")
    print("=" * 125)

if __name__ == "__main__":
    main()
