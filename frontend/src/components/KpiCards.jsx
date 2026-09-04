import React from 'react';
import { 
  AlertTriangle, 
  TrendingUp, 
  ShieldCheck, 
  Layers, 
  Zap, 
  FlaskConical,
  Percent
} from 'lucide-react';

export default function KpiCards({ overview, comparison }) {
  const atRisk = overview?.revenue_at_risk || 0;
  const aiRecovered = overview?.recovered_revenue_ai || 0;
  const aiTxRate = overview?.recovery_rate_ai || 0;
  const baseRecovered = overview?.recovered_revenue_baseline || 0;
  const baseTxRate = overview?.recovery_rate_baseline || 0;
  const overrides = overview?.policy_override_count || 0;
  const uplift = comparison?.uplift_revenue || (aiRecovered - baseRecovered > 0 ? aiRecovered - baseRecovered : 0);
  const retriesSaved = comparison?.retries_saved || 0;
  
  // Dynamically calculated Revenue Recovery Rate: (simulated recovered revenue / total revenue at risk) * 100
  const revenueRecoveryRate = atRisk > 0 ? (aiRecovered / atRisk) * 100 : 0;
  const baseRevenueRate = atRisk > 0 ? (baseRecovered / atRisk) * 100 : 0;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  return (
    <div className="space-y-4">
      
      {/* Prominent Simulation Mode Banner */}
      <div className="bg-sky-950/40 border border-sky-800/60 rounded-xl px-4 py-2.5 flex items-center gap-2.5 text-xs text-sky-200">
        <FlaskConical className="w-4 h-4 text-sky-400 shrink-0" />
        <div>
          <strong className="text-sky-300 font-semibold">SIMULATION MODE — </strong>
          <span>Synthetic payment data only. No real money, payment credentials, or live transactions are used. All financial figures represent simulated recovery outcomes.</span>
        </div>
      </div>

      {/* 5 KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        
        {/* 1. Revenue At Risk */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Revenue at Risk</span>
              <div className="w-8 h-8 rounded-lg bg-rose-950/60 border border-rose-800/60 flex items-center justify-center text-rose-400">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2.5">
              <div className="text-xl font-bold text-white tracking-tight">{formatINR(atRisk)}</div>
              <p className="text-[11px] text-slate-400 mt-0.5">Across 100 failed transactions</p>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-500">
            Total unrecovered failure exposure
          </div>
        </div>

        {/* 2. Simulated AI Recovery */}
        <div className="bg-slate-900/90 border border-sky-800/60 rounded-xl p-4 shadow-sm relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-sky-400 uppercase tracking-wider">Simulated AI Recovery</span>
              <div className="w-8 h-8 rounded-lg bg-sky-950/80 border border-sky-700/60 flex items-center justify-center text-sky-400">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2.5">
              <div className="text-xl font-bold text-sky-300 tracking-tight">{formatINR(aiRecovered)}</div>
              <div className="flex items-center gap-1.5 mt-0.5 text-xs">
                <span className="font-semibold text-emerald-400">{aiTxRate.toFixed(1)}%</span>
                <span className="text-slate-300 text-[11px]">transaction recovery</span>
              </div>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Revenue Recovery:</span>
            <span className="font-semibold text-sky-300">{revenueRecoveryRate.toFixed(1)}%</span>
          </div>
        </div>

        {/* 3. Naive Baseline */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Naive Baseline</span>
              <div className="w-8 h-8 rounded-lg bg-amber-950/60 border border-amber-800/60 flex items-center justify-center text-amber-400">
                <Layers className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2.5">
              <div className="text-xl font-bold text-slate-300 tracking-tight">{formatINR(baseRecovered)}</div>
              <div className="flex items-center gap-1.5 mt-0.5 text-xs">
                <span className="font-semibold text-amber-400">{baseTxRate.toFixed(1)}%</span>
                <span className="text-slate-400 text-[11px]">blind 3x retry rate</span>
              </div>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Revenue Recovery:</span>
            <span className="font-semibold text-amber-300/80">{baseRevenueRate.toFixed(1)}%</span>
          </div>
        </div>

        {/* 4. Simulated Uplift */}
        <div className="bg-slate-900/90 border border-emerald-800/60 rounded-xl p-4 shadow-sm relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/40 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Simulated Uplift</span>
              <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center text-emerald-400">
                <Zap className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2.5">
              <div className="text-xl font-bold text-emerald-300 tracking-tight">+{formatINR(uplift)}</div>
              <p className="text-[11px] text-emerald-400/90 mt-0.5 font-medium">
                Simulated Revenue Uplift vs. Naive Baseline
              </p>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Blind retries saved:</span>
            <span className="font-semibold text-emerald-300">{retriesSaved}</span>
          </div>
        </div>

        {/* 5. Policy Overrides & Guardrails */}
        <div className="bg-slate-900/90 border border-indigo-800/60 rounded-xl p-4 shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Policy Overrides</span>
              <div className="w-8 h-8 rounded-lg bg-indigo-950/80 border border-indigo-700/60 flex items-center justify-center text-indigo-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-2.5">
              <div className="text-xl font-bold text-indigo-300 tracking-tight">{overrides} Interventions</div>
              <p className="text-[11px] text-slate-400 mt-0.5">Deterministic Safety Guardrails</p>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-indigo-300/80">
            Unsafe/excessive retries blocked
          </div>
        </div>

      </div>
    </div>
  );
}
