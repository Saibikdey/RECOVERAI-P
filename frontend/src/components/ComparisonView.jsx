import React, { useState } from 'react';
import { 
  Sparkles, 
  Layers, 
  ShieldAlert, 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  HelpCircle,
  TrendingUp,
  UserX,
  FlaskConical,
  Binary,
  ChevronDown,
  ChevronUp,
  Table
} from 'lucide-react';

export default function ComparisonView({ comparison }) {
  const [showMultiSeed, setShowMultiSeed] = useState(false);
  const [multiSeedData, setMultiSeedData] = useState(null);
  const [loadingMultiSeed, setLoadingMultiSeed] = useState(false);

  if (!comparison) return null;

  const ai = comparison.ai_strategy;
  const blind = comparison.baseline_strategy;
  const rule = comparison.rule_baseline_strategy;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const aiRevenueRate = ai.total_revenue_at_risk > 0 
    ? (ai.total_recovered_revenue / ai.total_revenue_at_risk) * 100 
    : 0;

  const blindRevenueRate = blind.total_revenue_at_risk > 0 
    ? (blind.total_recovered_revenue / blind.total_revenue_at_risk) * 100 
    : 0;

  const ruleRevenueRate = rule && rule.total_revenue_at_risk > 0 
    ? (rule.total_recovered_revenue / rule.total_revenue_at_risk) * 100 
    : 0;

  const fetchMultiSeedEvaluation = async () => {
    if (multiSeedData) {
      setShowMultiSeed(!showMultiSeed);
      return;
    }
    setLoadingMultiSeed(true);
    try {
      const res = await fetch('/api/recovery/multi-seed-evaluation?seed_start=1&seed_end=20');
      if (res.ok) {
        const data = await res.json();
        setMultiSeedData(data);
        setShowMultiSeed(true);
      }
    } catch (e) {
      console.error('Multi-seed fetch error:', e);
    } finally {
      setLoadingMultiSeed(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Synthetic Simulation Assumptions & Baseline Disclaimer Banner */}
      <div className="bg-slate-900/90 border border-amber-800/40 rounded-xl p-4 text-xs text-amber-200/90 space-y-1.5 shadow-sm">
        <div className="flex items-center gap-2 font-semibold text-amber-300">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Simulation Methodology & 3-Way Comparative Evaluation</span>
        </div>
        <p className="text-slate-300">
          <span className="font-semibold text-amber-300">Assumption Notice:</span> {comparison.assumption_disclaimer}
        </p>
        <p className="text-slate-400">
          <span className="font-semibold text-slate-300">Evaluation Strategy Notice:</span> We evaluate RecoverAI against two distinct baselines: (1) Blind 3x Retries without diagnosis, and (2) Static Rule-Based recovery without contextual AI.
        </p>
      </div>

      {/* 3-Way Side-by-Side Strategy Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Card 1: RecoverAI Agent (AI + Deterministic Guardrails) */}
        <div className="bg-slate-900/90 border-2 border-sky-500/60 rounded-2xl p-5 shadow-xl relative overflow-hidden bg-gradient-to-b from-slate-900 via-slate-900 to-sky-950/30 flex flex-col justify-between">
          <div>
            <div className="absolute top-0 right-0 px-3 py-1 bg-sky-600 text-[10px] font-bold text-white rounded-bl-xl uppercase tracking-wider">
              Smart Policy-Enforced
            </div>

            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-center text-sky-400">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{ai.name}</h3>
                <p className="text-[11px] text-slate-400">AI root-cause diagnosis + strict policy guardrails</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 my-4 bg-slate-950/70 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Simulated Recovered</span>
                <div className="text-xl font-bold text-sky-300 mt-0.5">{formatINR(ai.total_recovered_revenue)}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  <span className="text-sky-400 font-semibold">{aiRevenueRate.toFixed(1)}%</span> of risk
                </div>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Recovery Rate</span>
                <div className="text-xl font-bold text-emerald-400 mt-0.5">{ai.recovery_rate_pct.toFixed(1)}%</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  <span className="text-emerald-400 font-semibold">{ai.recovered_count}</span> of {ai.total_failed_count} txs
                </div>
              </div>
            </div>

            {/* Key Attributes */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-sky-400" /> Targeted Retries
                </span>
                <span className="font-semibold text-white">{ai.total_retries_executed}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Policy Guardrail Overrides
                </span>
                <span className="font-semibold text-emerald-300">{ai.overrides_enforced}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" /> Fraud Contained
                </span>
                <span className="font-semibold text-indigo-300">{ai.fraud_blocks}</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-purple-400" /> VIP / Tier Escalations
                </span>
                <span className="font-semibold text-purple-300">{ai.escalations_count}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Simple Rule-Based Baseline */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden bg-gradient-to-b from-slate-900 via-slate-900 to-purple-950/20 flex flex-col justify-between">
          <div>
            <div className="absolute top-0 right-0 px-3 py-1 bg-purple-900/80 text-[10px] font-bold text-purple-200 rounded-bl-xl uppercase tracking-wider">
              Static Rule-Based
            </div>

            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                <Binary className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-200">{rule?.name || 'Simple Rule-Based'}</h3>
                <p className="text-[11px] text-purple-300/80">Static deterministic rules without AI context</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 my-4 bg-slate-950/70 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Simulated Recovered</span>
                <div className="text-xl font-bold text-slate-300 mt-0.5">{formatINR(rule?.total_recovered_revenue || 0)}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  <span className="text-purple-300/80 font-semibold">{ruleRevenueRate.toFixed(1)}%</span> of risk
                </div>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Recovery Rate</span>
                <div className="text-xl font-bold text-purple-400 mt-0.5">{(rule?.recovery_rate_pct || 0).toFixed(1)}%</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  <span className="text-purple-300 font-semibold">{rule?.recovered_count || 0}</span> of {rule?.total_failed_count || 100} txs
                </div>
              </div>
            </div>

            {/* Key Attributes */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-purple-400" /> Retries Executed
                </span>
                <span className="font-semibold text-purple-300">{rule?.total_retries_executed || 0}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-purple-400" /> Contextual Reasoning
                </span>
                <span className="font-semibold text-slate-400">None (Fixed error map)</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-purple-400" /> Fraud Contained
                </span>
                <span className="font-semibold text-purple-300">{rule?.fraud_blocks || 0}</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> RecoverAI Uplift
                </span>
                <span className="font-semibold text-emerald-400">+{comparison.uplift_over_rule_rate_pct.toFixed(1)}% ({formatINR(comparison.uplift_over_rule_revenue)})</span>
              </div>
            </div>
          </div>
        </div>

        {/* Card 3: Naive Blind Retry Baseline */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden bg-gradient-to-b from-slate-900 via-slate-900 to-amber-950/20 flex flex-col justify-between">
          <div>
            <div className="absolute top-0 right-0 px-3 py-1 bg-amber-900/80 text-[10px] font-bold text-amber-200 rounded-bl-xl uppercase tracking-wider">
              Blind Retry Baseline
            </div>

            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-200">{blind.name}</h3>
                <p className="text-[11px] text-amber-300/80">Blind 3x retries without diagnosis or policy</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 my-4 bg-slate-950/70 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Simulated Recovered</span>
                <div className="text-xl font-bold text-slate-300 mt-0.5">{formatINR(blind.total_recovered_revenue)}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  <span className="text-amber-300/80 font-semibold">{blindRevenueRate.toFixed(1)}%</span> of risk
                </div>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 font-medium">Recovery Rate</span>
                <div className="text-xl font-bold text-amber-400 mt-0.5">{blind.recovery_rate_pct.toFixed(1)}%</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  <span className="text-amber-300 font-semibold">{blind.recovered_count}</span> of {blind.total_failed_count} txs
                </div>
              </div>
            </div>

            {/* Key Attributes */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-amber-400" /> Total Blind Retries
                </span>
                <span className="font-semibold text-amber-300">{blind.total_retries_executed}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <XCircle className="w-3.5 h-3.5 text-rose-400" /> Wasted Failed Retries
                </span>
                <span className="font-semibold text-rose-300">{blind.unnecessary_failed_retries}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <UserX className="w-3.5 h-3.5 text-rose-400" /> Customer Fatigue Risk
                </span>
                <span className="font-semibold text-rose-300">HIGH (Blind re-attempts)</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> RecoverAI Uplift
                </span>
                <span className="font-semibold text-emerald-400">+{comparison.uplift_rate_pct.toFixed(1)}% ({formatINR(comparison.uplift_revenue)})</span>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* Net Uplift Summary Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        <div className="bg-gradient-to-r from-emerald-950/60 to-slate-900 border border-emerald-700/50 rounded-xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center text-emerald-400 shrink-0">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Uplift vs. Blind Retries</div>
            <div className="text-lg font-bold text-emerald-300">+{formatINR(comparison.uplift_revenue)}</div>
            <div className="text-[11px] text-emerald-400 font-semibold">+{comparison.uplift_rate_pct.toFixed(1)}% recovery rate</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-950/60 to-slate-900 border border-purple-700/50 rounded-xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-400/40 flex items-center justify-center text-purple-400 shrink-0">
            <Binary className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Uplift vs. Rule Baseline</div>
            <div className="text-lg font-bold text-purple-300">+{formatINR(comparison.uplift_over_rule_revenue)}</div>
            <div className="text-[11px] text-purple-400 font-semibold">+{comparison.uplift_over_rule_rate_pct.toFixed(1)}% recovery rate</div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-sky-950/60 to-slate-900 border border-sky-700/50 rounded-xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-center text-sky-400 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">Blind Retries Saved</div>
            <div className="text-lg font-bold text-sky-300">{comparison.retries_saved} Wasted Retries</div>
            <div className="text-[11px] text-sky-400 font-semibold">{comparison.customer_fatigue_prevented} fatigue events avoided</div>
          </div>
        </div>

      </div>

      {/* Multi-Seed Robustness Evaluation Drawer */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <button
          onClick={fetchMultiSeedEvaluation}
          className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-850/80 transition bg-slate-900"
        >
          <div className="flex items-center gap-2.5">
            <FlaskConical className="w-4 h-4 text-sky-400" />
            <div>
              <span className="text-xs font-bold text-slate-200">
                Multi-Seed Robustness Evaluation (20 Pseudo-Random Seeds, 2,000 Transactions)
              </span>
              <p className="text-[11px] text-slate-400">
                Shows the gap between strategies, under the documented synthetic probability model, holds consistently across 20 different random transaction mixes — not an artifact of seed 42. Not a claim of real-world statistical significance.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-sky-400 font-medium">
            <span>{loadingMultiSeed ? 'Computing 20 Seeds...' : (showMultiSeed ? 'Hide Results' : 'View 20-Seed Analysis')}</span>
            {showMultiSeed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {showMultiSeed && multiSeedData && (
          <div className="p-5 border-t border-slate-800 bg-slate-950/60 space-y-4">
            
            {/* Aggregate Stats Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">RecoverAI Mean Rate</span>
                <div className="text-lg font-bold text-sky-300 mt-0.5">{multiSeedData.ai_mean_recovery_rate}%</div>
                <div className="text-[10px] text-slate-400">Range: {multiSeedData.ai_min_recovery_rate}% – {multiSeedData.ai_max_recovery_rate}%</div>
              </div>
              <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Mean Uplift vs Rule</span>
                <div className="text-lg font-bold text-purple-300 mt-0.5">+{multiSeedData.mean_uplift_over_rule_rate}%</div>
                <div className="text-[10px] text-purple-400/80">+{formatINR(multiSeedData.mean_uplift_over_rule_revenue)} mean</div>
              </div>
              <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Mean Uplift vs Blind</span>
                <div className="text-lg font-bold text-emerald-300 mt-0.5">+{multiSeedData.mean_uplift_over_blind_rate}%</div>
                <div className="text-[10px] text-emerald-400/80">+{formatINR(multiSeedData.mean_uplift_over_blind_revenue)} mean</div>
              </div>
              <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Std. Deviation</span>
                <div className="text-lg font-bold text-slate-300 mt-0.5">±{multiSeedData.std_dev_recovery_rate}%</div>
                <div className="text-[10px] text-slate-400">High consistency across seeds</div>
              </div>
            </div>

            {/* Detailed Per-Seed Table */}
            <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-lg text-xs font-mono">
              <table className="w-full text-left">
                <thead className="bg-slate-900 text-slate-400 sticky top-0 border-b border-slate-800">
                  <tr>
                    <th className="p-2">Seed</th>
                    <th className="p-2">Risk (INR)</th>
                    <th className="p-2">Blind Rate</th>
                    <th className="p-2">Rule Rate</th>
                    <th className="p-2 text-sky-400">RecoverAI Rate</th>
                    <th className="p-2 text-purple-400">Uplift v Rule</th>
                    <th className="p-2 text-emerald-400">Uplift v Blind</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {multiSeedData.per_seed_results.map((r) => (
                    <tr key={r.seed} className="hover:bg-slate-900/50">
                      <td className="p-2 font-bold text-slate-300">Seed {r.seed}</td>
                      <td className="p-2 text-slate-400">₹{r.total_revenue_at_risk.toLocaleString('en-IN')}</td>
                      <td className="p-2 text-amber-400/80">{r.blind_recovery_rate}%</td>
                      <td className="p-2 text-purple-300">{r.rule_recovery_rate}%</td>
                      <td className="p-2 font-bold text-sky-300">{r.ai_recovery_rate}%</td>
                      <td className="p-2 font-semibold text-purple-400">+{r.uplift_over_rule_pct}%</td>
                      <td className="p-2 font-semibold text-emerald-400">+{r.uplift_over_blind_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </div>
        )}
      </div>

    </div>
  );
}
