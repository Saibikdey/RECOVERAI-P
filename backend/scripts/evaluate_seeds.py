#!/usr/bin/env python3
"""
RecoverAI Multi-Seed Statistical Evaluation Script
Evaluates RecoverAI (AI + Policy Engine) vs Baseline 1 (Blind Retry) vs Baseline 2 (Rule-Based)
across 20 pseudo-random dataset seeds to demonstrate variance and statistical validity.
"""

import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.orchestrator import RecoveryOrchestrator

def main():
    print("=" * 80)
    print("      RECOVERAI: 20-SEED STATISTICAL EVALUATION ACROSS SIMULATED DATASETS      ")
    print("=" * 80)
    print("Running evaluation across seeds 1 to 20 (100 synthetic payments per seed)...")
    print("-" * 80)

    res = RecoveryOrchestrator.run_multi_seed_evaluation(seed_start=1, seed_end=20, count_per_seed=100)

    # Print Table Header
    print(f"{'Seed':<6} | {'Risk Amount':<14} | {'Blind Rate':<11} | {'Rule Rate':<10} | {'AI Rate':<9} | {'Uplift v Blind':<15} | {'Uplift v Rule':<15}")
    print("-" * 90)

    for item in res.per_seed_results:
        print(f"{item['seed']:<6} | ₹{item['total_revenue_at_risk']:>12,.2f} | {item['blind_recovery_rate']:>10.1f}% | {item['rule_recovery_rate']:>9.1f}% | {item['ai_recovery_rate']:>8.1f}% | {item['uplift_over_blind_pct']:>+13.1f}% | {item['uplift_over_rule_pct']:>+13.1f}%")

    print("=" * 90)
    print("                               AGGREGATE SUMMARY                                ")
    print("=" * 90)
    print(f"Total Datasets Evaluated       : {res.seed_count} independent seeds (2,000 transactions)")
    print(f"RecoverAI Mean Recovery Rate   : {res.ai_mean_recovery_rate:.2f}% (Range: {res.ai_min_recovery_rate:.1f}% - {res.ai_max_recovery_rate:.1f}%, StdDev: {res.std_dev_recovery_rate:.2f}%)")
    print(f"RecoverAI Mean Revenue Recover : ₹{res.ai_mean_recovered_revenue:,.2f}")
    print(f"Rule-Based Mean Recovery Rate  : {res.rule_mean_recovery_rate:.2f}% (Mean Revenue: ₹{res.rule_mean_recovered_revenue:,.2f})")
    print(f"Blind Retry Mean Recovery Rate : {res.blind_mean_recovery_rate:.2f}% (Mean Revenue: ₹{res.blind_mean_recovered_revenue:,.2f})")
    print("-" * 90)
    print(f"Mean Uplift over Blind Retry   : +{res.mean_uplift_over_blind_rate:.2f}% transaction recovery (+₹{res.mean_uplift_over_blind_revenue:,.2f})")
    print(f"Mean Uplift over Rule Baseline : +{res.mean_uplift_over_rule_rate:.2f}% transaction recovery (+₹{res.mean_uplift_over_rule_revenue:,.2f})")
    print("=" * 90)
    print("\n* All figures are derived from documented synthetic domain simulation assumptions.")

if __name__ == "__main__":
    main()
