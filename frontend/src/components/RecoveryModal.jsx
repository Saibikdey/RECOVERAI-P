import React from 'react';
import { 
  X, 
  Sparkles, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  AlertCircle, 
  HelpCircle, 
  Zap, 
  Activity, 
  Cpu,
  Lock,
  Binary
} from 'lucide-react';

export default function RecoveryModal({ 
  isOpen, 
  onClose, 
  payment, 
  pipelineResult, 
  isProcessing 
}) {
  if (!isOpen) return null;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const getActionBadgeClass = (action) => {
    switch (action) {
      case 'RETRY':
        return 'bg-blue-950 text-blue-400 border-blue-700';
      case 'ALTERNATE_PAYMENT':
        return 'bg-emerald-950 text-emerald-400 border-emerald-700';
      case 'REMINDER':
        return 'bg-amber-950 text-amber-400 border-amber-700';
      case 'ESCALATE':
        return 'bg-purple-950 text-purple-400 border-purple-700';
      case 'NO_ACTION':
        return 'bg-rose-950 text-rose-400 border-rose-700';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden my-6">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-500/20 border border-sky-400/30 flex items-center justify-center text-sky-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Live Recovery Pipeline Trace: <span className="text-sky-400">{payment?.transaction_id}</span>
              </h3>
              <p className="text-xs text-slate-400">
                AI Diagnosis $\rightarrow$ Policy Authorization $\rightarrow$ Outcome Simulation
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Boundary Anchor Banner */}
        <div className="bg-gradient-to-r from-sky-950/80 via-slate-900 to-indigo-950/80 px-6 py-2 border-b border-slate-800 flex items-center justify-between text-xs">
          <span className="font-bold text-sky-300 tracking-wide flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" /> AI RECOMMENDS.
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 ml-2" /> POLICY ENGINE DECIDES.
          </span>
          <span className="text-[11px] text-slate-400 bg-slate-950/70 px-2 py-0.5 rounded border border-slate-800">
            Deterministic Final Authority
          </span>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-5 max-h-[72vh] overflow-y-auto">
          
          {isProcessing ? (
            <div className="py-16 text-center space-y-3">
              <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-sm font-semibold text-slate-300">Executing Recovery Workflow...</p>
              <p className="text-xs text-slate-500">Evaluating LLM Root-Cause & Deterministic Safety Rules</p>
            </div>
          ) : pipelineResult ? (
            <>
              {/* Idempotency Duplicate Alert Banner if duplicate */}
              {pipelineResult.is_duplicate && (
                <div className="bg-rose-950/80 border border-rose-600 rounded-xl p-3.5 text-xs text-rose-200 flex items-center gap-3">
                  <Lock className="w-5 h-5 text-rose-400 shrink-0" />
                  <div>
                    <span className="font-bold text-rose-100">IDEMPOTENCY GUARD: DUPLICATE EXECUTION BLOCKED</span>
                    <p className="text-rose-300 mt-0.5">{pipelineResult.message}</p>
                  </div>
                </div>
              )}

              {/* Stage 1: Failed Payment Context */}
              <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px]">1</span>
                    Payment Failure Context
                  </span>
                  <span className="text-xs px-2.5 py-0.5 rounded bg-rose-950/80 text-rose-400 border border-rose-800 font-mono font-semibold">
                    {payment?.error_code}
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mt-3">
                  <div>
                    <span className="text-slate-500">Customer:</span>
                    <div className="font-semibold text-white">{payment?.customer_name}</div>
                    <span className="text-[10px] text-sky-400">{payment?.customer_tier} Tier</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Amount at Risk:</span>
                    <div className="font-semibold text-white">{formatINR(payment?.amount)}</div>
                  </div>
                  <div>
                    <span className="text-slate-500">Payment Method:</span>
                    <div className="font-semibold text-slate-300">{payment?.payment_method}</div>
                  </div>
                  <div>
                    <span className="text-slate-500">Prior Retries:</span>
                    <div className="font-semibold text-slate-300">{payment?.retry_count} / 3 max</div>
                  </div>
                </div>
                <div className="mt-3 text-xs bg-slate-900/80 p-2.5 rounded border border-slate-800/80 text-slate-300 flex items-center justify-between">
                  <div>
                    <span className="text-slate-500 font-mono">Gateway Message: </span>
                    <span className="text-slate-200">{payment?.error_message}</span>
                  </div>
                  {pipelineResult.event_id && (
                    <span className="text-[10px] text-slate-500 font-mono">Event: {pipelineResult.event_id}</span>
                  )}
                </div>
              </div>

              {/* Stage 2: AI Diagnostic Layer (Advisory Only) */}
              <div className="bg-slate-950/60 rounded-xl p-4 border border-sky-900/40 relative">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded-full bg-sky-950 text-sky-300 border border-sky-700 flex items-center justify-center text-[10px]">2</span>
                      AI Diagnostic Layer
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-sky-950/90 text-sky-300 border border-sky-700 font-medium">
                      Advisory Recommendation Only
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className="text-xs text-slate-400"
                      title="Internal decision signal used by the policy confidence threshold — not a calibrated real-world accuracy probability."
                    >
                      Confidence: <strong className="text-sky-300 font-bold">{(pipelineResult.llm_diagnosis.confidence * 100).toFixed(0)}%</strong>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-700">
                      {pipelineResult.llm_mode}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-slate-200 mt-2 bg-slate-900/80 p-3 rounded border border-slate-800">
                  <p className="font-medium text-slate-100">{pipelineResult.llm_diagnosis.root_cause_diagnosis}</p>
                  <p className="text-slate-400 mt-1.5 text-[11px]">
                    <strong className="text-slate-300">Contextual Rationale: </strong>{pipelineResult.llm_diagnosis.rationale}
                  </p>
                </div>

                <div className="mt-3 flex items-center justify-between text-xs bg-slate-900/50 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-400">AI Advisory Recommendation:</span>
                  <span className={`px-2.5 py-0.5 rounded text-xs font-bold border ${getActionBadgeClass(pipelineResult.llm_diagnosis.recommended_action)}`}>
                    {pipelineResult.llm_diagnosis.recommended_action}
                  </span>
                </div>
              </div>

              {/* Stage 3: Deterministic Policy Engine (FINAL AUTHORITY) */}
              <div className={`rounded-xl p-4 border ${
                pipelineResult.policy_evaluation.is_overridden 
                  ? 'bg-amber-950/30 border-amber-700/60' 
                  : 'bg-emerald-950/30 border-emerald-700/60'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-200">
                      <span className="w-4 h-4 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-700 flex items-center justify-center text-[10px]">3</span>
                      Deterministic Policy Engine
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-emerald-300 border border-emerald-700 font-bold">
                      THE FINAL AUTHORITY
                    </span>
                  </div>
                  {pipelineResult.policy_evaluation.is_overridden ? (
                    <span className="flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-600 font-semibold">
                      <ShieldAlert className="w-3.5 h-3.5" /> Policy Guardrail Override
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-600 font-semibold">
                      <ShieldCheck className="w-3.5 h-3.5" /> Approved by Policy
                    </span>
                  )}
                </div>

                {pipelineResult.policy_evaluation.is_overridden && (
                  <div className="bg-amber-950/70 border border-amber-700/90 p-3 rounded-lg text-xs text-amber-200 my-2">
                    <strong className="text-amber-100">Guardrail Intervention Reason: </strong>
                    {pipelineResult.policy_evaluation.override_reason}
                  </div>
                )}

                <div className="flex items-center justify-between my-2 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-300 font-medium">Final Policy-Authorized Action:</span>
                  <div className={`px-3 py-1 rounded text-xs font-bold border ${getActionBadgeClass(pipelineResult.policy_evaluation.approved_action)}`}>
                    {pipelineResult.policy_evaluation.approved_action}
                  </div>
                </div>

                {/* Applied Policy Rules List */}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {pipelineResult.policy_evaluation.applied_rules?.map((rule, idx) => (
                    <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-slate-900/90 text-slate-300 border border-slate-700 font-mono">
                      {rule}
                    </span>
                  ))}
                </div>
              </div>

              {/* Stage 4: Simulated Execution & Outcome */}
              <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-[10px]">4</span>
                    Simulated Recovery Outcome
                  </span>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${
                    pipelineResult.simulation_outcome.status === 'RECOVERED'
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                      : pipelineResult.simulation_outcome.status === 'DUPLICATE_BLOCKED'
                      ? 'bg-rose-950 text-rose-300 border-rose-700'
                      : 'bg-amber-950 text-amber-300 border-amber-700'
                  }`}>
                    {pipelineResult.simulation_outcome.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs mt-3 bg-slate-900/80 p-3 rounded border border-slate-800">
                  <div>
                    <span className="text-slate-500">Simulated Recovered Amount:</span>
                    <div className="text-base font-bold text-emerald-400 mt-0.5">
                      {formatINR(pipelineResult.simulation_outcome.recovered_amount)}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500">Simulated Success Probability:</span>
                    <div className="text-base font-bold text-white mt-0.5">
                      {(pipelineResult.simulation_outcome.simulated_probability * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                <p className="text-xs text-slate-400 mt-2 italic">
                  * {pipelineResult.simulation_outcome.notes}
                </p>
              </div>

            </>
          ) : null}

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
