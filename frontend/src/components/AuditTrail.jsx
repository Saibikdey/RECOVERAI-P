import React, { useState } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Filter, 
  Clock, 
  ArrowRight,
  AlertTriangle,
  Lock
} from 'lucide-react';

export default function AuditTrail({ auditLogs, onRefresh }) {
  const [filterMode, setFilterMode] = useState('ALL'); // 'ALL', 'OVERRIDES', 'DUPLICATES'

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const filteredLogs = auditLogs.filter(log => {
    if (filterMode === 'OVERRIDES') return log.policy_override;
    if (filterMode === 'DUPLICATES') return log.duplicate_blocked;
    return true;
  });

  const overridesCount = auditLogs.filter(l => l.policy_override).length;
  const duplicatesCount = auditLogs.filter(l => l.duplicate_blocked).length;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl shadow-md overflow-hidden">
      
      {/* Header / Filter Toolbar */}
      <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-950/40">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Decision Audit Trail & Guardrail Log
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Immutable log recording every LLM recommendation, policy evaluation, and outcome
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* All Filter */}
          <button
            onClick={() => setFilterMode('ALL')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition ${
              filterMode === 'ALL'
                ? 'bg-sky-600 text-white border-sky-500 shadow-sm'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
            }`}
          >
            All Logs ({auditLogs.length})
          </button>

          {/* Overrides Toggle */}
          <button
            onClick={() => setFilterMode('OVERRIDES')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition ${
              filterMode === 'OVERRIDES'
                ? 'bg-amber-950 text-amber-300 border-amber-600 shadow-sm shadow-amber-950'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Overrides ({overridesCount})
          </button>

          {/* Duplicates Toggle */}
          <button
            onClick={() => setFilterMode('DUPLICATES')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border transition ${
              filterMode === 'DUPLICATES'
                ? 'bg-rose-950 text-rose-300 border-rose-600 shadow-sm shadow-rose-950'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            Duplicates Blocked ({duplicatesCount})
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
            <tr>
              <th className="px-4 py-3">Event / Tx ID</th>
              <th className="px-4 py-3">LLM Diagnosis</th>
              <th className="px-4 py-3">LLM Proposed</th>
              <th className="px-4 py-3">Policy Approved</th>
              <th className="px-4 py-3">Policy Guardrail State</th>
              <th className="px-4 py-3">Outcome</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan="6" className="text-center py-10 text-slate-500">
                  {filterMode === 'OVERRIDES' 
                    ? 'No policy override events recorded.' 
                    : filterMode === 'DUPLICATES'
                    ? 'No duplicate-blocked events recorded.'
                    : 'No recovery decisions recorded. Run AI Recovery or diagnose a transaction to generate audit logs.'}
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                  
                  {/* Event & Tx */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="font-mono text-sky-400 font-medium text-[11px]">{log.transaction_id}</div>
                    {log.event_id && (
                      <div className="font-mono text-slate-500 text-[9px] truncate max-w-[130px]" title={log.event_id}>
                        {log.event_id}
                      </div>
                    )}
                    <div className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3" />
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                  </td>

                  {/* Diagnosis */}
                  <td className="px-4 py-3 max-w-xs">
                    <div className="text-slate-200 text-xs line-clamp-2" title={log.llm_diagnosis}>
                      {log.llm_diagnosis}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-slate-400">
                        Conf: <strong className="text-white">{(log.llm_confidence * 100).toFixed(0)}%</strong>
                      </span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-950 text-slate-400 border border-slate-800">
                        {log.llm_mode}
                      </span>
                    </div>
                  </td>

                  {/* LLM Proposed */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                      {log.llm_action_recommended}
                    </span>
                  </td>

                  {/* Policy Approved */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                      log.duplicate_blocked
                        ? 'bg-rose-950 text-rose-300 border-rose-700'
                        : log.policy_override
                        ? 'bg-amber-950 text-amber-300 border-amber-700'
                        : 'bg-emerald-950 text-emerald-300 border-emerald-700'
                    }`}>
                      {log.policy_action_approved}
                    </span>
                  </td>

                  {/* Policy Guardrail Status & Override Reason */}
                  <td className="px-4 py-3 max-w-sm">
                    {log.duplicate_blocked ? (
                      <div className="bg-rose-950/40 border border-rose-800/60 p-1.5 rounded text-[11px] text-rose-300 flex items-start gap-1.5">
                        <Lock className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                        <span>{log.policy_override_reason || 'Duplicate event blocked by Idempotency Guard'}</span>
                      </div>
                    ) : log.policy_override ? (
                      <div className="bg-amber-950/40 border border-amber-800/60 p-1.5 rounded text-[11px] text-amber-300 flex items-start gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                        <span>{log.policy_override_reason}</span>
                      </div>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                        Rules Validated & Approved
                      </span>
                    )}
                  </td>

                  {/* Outcome */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    {log.simulation_status === 'DUPLICATE_BLOCKED' ? (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                        <Lock className="w-3.5 h-3.5" /> DUPLICATE BLOCKED
                      </span>
                    ) : log.simulation_status === 'RECOVERED' ? (
                      <div>
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                          <CheckCircle2 className="w-3.5 h-3.5" /> RECOVERED
                        </span>
                        {log.recovered_amount > 0 && (
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            +{formatINR(log.recovered_amount)}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                        <XCircle className="w-3.5 h-3.5" /> FAILED
                      </span>
                    )}
                  </td>

                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}
