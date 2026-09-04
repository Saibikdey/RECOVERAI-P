import React from 'react';
import { 
  ShieldCheck, 
  Sparkles, 
  RotateCcw, 
  Play, 
  Layers, 
  Activity, 
  Info, 
  ShieldAlert,
  HelpCircle,
  FlaskConical,
  Binary
} from 'lucide-react';

export default function Header({
  llmMode,
  onRunBatch,
  onRunBaseline,
  onRunRuleBaseline,
  onReset,
  loadingBatch,
  loadingBaseline,
  loadingRuleBaseline,
  loadingReset
}) {
  const isLlm = llmMode && llmMode.includes("LLM Mode") && !llmMode.includes("Fallback");

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md sticky top-0 z-30 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
        
        {/* Brand & Subtitle */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold text-xl shrink-0">
            R
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">RecoverAI</h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-950 text-sky-400 border border-sky-800 font-medium whitespace-nowrap">
                Razorpay AI Track 03
              </span>
              
              {/* Dynamic LLM / Deterministic Mode Badge */}
              <div className={`flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-semibold border whitespace-nowrap ${
                isLlm 
                  ? 'bg-emerald-950/80 text-emerald-400 border-emerald-700' 
                  : 'bg-amber-950/80 text-amber-300 border-amber-700'
              }`}>
                <span className={`w-2 h-2 rounded-full ${isLlm ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
                {llmMode || "Deterministic Fallback Mode"}
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Autonomous Revenue Recovery Agent with Deterministic Policy Guardrails
            </p>
          </div>
        </div>

        {/* Global CTA Actions */}
        <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto justify-start lg:justify-end">
          <button
            onClick={onReset}
            disabled={loadingReset || loadingBatch || loadingBaseline || loadingRuleBaseline}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 rounded-lg transition disabled:opacity-50 shadow-sm"
            title="Reset dataset with 100 fresh synthetic failed payments"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loadingReset ? 'animate-spin' : ''}`} />
            Reset (100)
          </button>

          <button
            onClick={onRunBaseline}
            disabled={loadingReset || loadingBatch || loadingBaseline || loadingRuleBaseline}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-amber-200 bg-amber-950/70 hover:bg-amber-900/80 active:bg-amber-800 border border-amber-700/80 rounded-lg transition disabled:opacity-50 shadow-sm"
            title="Simulate blind 3x retries without diagnosis or guardrails"
          >
            <Layers className={`w-3.5 h-3.5 ${loadingBaseline ? 'animate-spin' : ''}`} />
            1. Blind Retry
          </button>

          <button
            onClick={onRunRuleBaseline}
            disabled={loadingReset || loadingBatch || loadingBaseline || loadingRuleBaseline}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-purple-200 bg-purple-950/70 hover:bg-purple-900/80 active:bg-purple-800 border border-purple-700/80 rounded-lg transition disabled:opacity-50 shadow-sm"
            title="Simulate simple static rule-based recovery"
          >
            <Binary className={`w-3.5 h-3.5 ${loadingRuleBaseline ? 'animate-spin' : ''}`} />
            2. Rule Baseline
          </button>

          <button
            onClick={onRunBatch}
            disabled={loadingReset || loadingBatch || loadingBaseline || loadingRuleBaseline}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 active:from-sky-700 active:to-indigo-700 rounded-lg shadow-md shadow-sky-600/30 transition disabled:opacity-50"
            title="Run AI Diagnosis & Policy Recovery across all 100 records"
          >
            <Sparkles className={`w-3.5 h-3.5 ${loadingBatch ? 'animate-spin' : ''}`} />
            {loadingBatch ? 'Simulating...' : '3. Run RecoverAI'}
          </button>
        </div>

      </div>

      {/* Why AI & Safety Banner */}
      <div className="max-w-7xl mx-auto mt-3 pt-2.5 border-t border-slate-800/80 flex flex-col md:flex-row items-start md:items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sky-400 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 shrink-0" /> Why AI?
          </span>
          <span>AI performs contextual root-cause diagnosis and recommends an action; deterministic rules validate and authorize the action.</span>
        </div>
        <div className="flex items-center gap-1.5 text-slate-300 bg-slate-950/70 px-2.5 py-1 rounded-md border border-slate-800 text-[11px] whitespace-nowrap">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span>Policy Engine Invariant: LLM has zero direct financial authority</span>
        </div>
      </div>
    </header>
  );
}
