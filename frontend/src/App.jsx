import React, { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import KpiCards from './components/KpiCards.jsx';
import ComparisonView from './components/ComparisonView.jsx';
import TransactionTable from './components/TransactionTable.jsx';
import RecoveryModal from './components/RecoveryModal.jsx';
import AuditTrail from './components/AuditTrail.jsx';
import ArchitectureView from './components/ArchitectureView.jsx';
import { 
  BarChart3, 
  ListOrdered, 
  ShieldCheck, 
  Cpu, 
  RefreshCw,
  PieChart,
  Layers,
  AlertCircle
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'payments', 'audit', 'architecture'
  const [overview, setOverview] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [payments, setPayments] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [health, setHealth] = useState(null);
  const [fetchError, setFetchError] = useState(null);
  
  // Loading States
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingBatch, setLoadingBatch] = useState(false);
  const [loadingBaseline, setLoadingBaseline] = useState(false);
  const [loadingRuleBaseline, setLoadingRuleBaseline] = useState(false);
  const [loadingReset, setLoadingReset] = useState(false);
  const [loadingPaymentId, setLoadingPaymentId] = useState(null);

  // Modal State for Single Diagnostic
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isModalProcessing, setIsModalProcessing] = useState(false);

  // Fetch all state from backend
  const fetchAllData = async () => {
    try {
      setFetchError(null);
      const apiFetch = async (endpoint) => {
        try {
          const res = await fetch(`${API_BASE}${endpoint}`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return await res.json();
        } catch (e) {
          const res = await fetch(endpoint);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          return await res.json();
        }
      };

      const [healthRes, overviewRes, compRes, paymentsRes, auditRes] = await Promise.all([
        apiFetch('/api/health'),
        apiFetch('/api/analytics/overview'),
        apiFetch('/api/recovery/comparison'),
        apiFetch('/api/payments'),
        apiFetch('/api/audit?limit=200')
      ]);

      setHealth(healthRes);
      setOverview(overviewRes);
      setComparison(compRes);
      setPayments(paymentsRes);
      setAuditLogs(auditRes);
    } catch (err) {
      console.error('Error loading RecoverAI data:', err);
      setFetchError(err.message || 'Failed to connect to RecoverAI backend API');
    } finally {
      setLoadingInitial(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const apiPost = async (endpoint, body = null) => {
    const opts = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined
    };
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, opts);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      const res = await fetch(endpoint, opts);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    }
  };

  // Handler: Run AI Recovery Batch (100 Records)
  const handleRunBatch = async () => {
    setLoadingBatch(true);
    try {
      await apiPost('/api/recovery/batch');
      await fetchAllData();
    } catch (err) {
      console.error('Batch recovery error:', err);
      setFetchError(`Batch recovery failed: ${err.message}`);
    } finally {
      setLoadingBatch(false);
    }
  };

  // Handler: Run Baseline 1: Naive Blind Retry Simulation
  const handleRunBaseline = async () => {
    setLoadingBaseline(true);
    try {
      await apiPost('/api/recovery/baseline');
      await fetchAllData();
    } catch (err) {
      console.error('Baseline error:', err);
      setFetchError(`Baseline simulation failed: ${err.message}`);
    } finally {
      setLoadingBaseline(false);
    }
  };

  // Handler: Run Baseline 2: Simple Rule-Based Simulation
  const handleRunRuleBaseline = async () => {
    setLoadingRuleBaseline(true);
    try {
      await apiPost('/api/recovery/rule-baseline');
      await fetchAllData();
    } catch (err) {
      console.error('Rule Baseline error:', err);
      setFetchError(`Rule baseline simulation failed: ${err.message}`);
    } finally {
      setLoadingRuleBaseline(false);
    }
  };

  // Handler: Reset Dataset (100 fresh records)
  const handleReset = async () => {
    setLoadingReset(true);
    try {
      await apiPost('/api/payments/reset');
      await fetchAllData();
    } catch (err) {
      console.error('Reset error:', err);
      setFetchError(`Reset failed: ${err.message}`);
    } finally {
      setLoadingReset(false);
    }
  };

  // Handler: Diagnose & Recover Single Payment (Live Modal)
  const handleDiagnosePayment = async (payment) => {
    setSelectedPayment(payment);
    setIsModalOpen(true);
    setIsModalProcessing(true);
    setLoadingPaymentId(payment.id);

    try {
      const data = await apiPost(`/api/recovery/diagnose/${payment.id}`);
      setPipelineResult(data);
      await fetchAllData();
    } catch (err) {
      console.error('Single diagnosis error:', err);
      setFetchError(`Single diagnosis failed: ${err.message}`);
    } finally {
      setIsModalProcessing(false);
      setLoadingPaymentId(null);
    }
  };

  if (loadingInitial) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
        <div className="text-slate-300 text-sm font-semibold tracking-wide">
          Connecting to RecoverAI Recovery Engine...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      
      {/* Top Header */}
      <Header
        llmMode={health?.llm_mode}
        onRunBatch={handleRunBatch}
        onRunBaseline={handleRunBaseline}
        onRunRuleBaseline={handleRunRuleBaseline}
        onReset={handleReset}
        loadingBatch={loadingBatch}
        loadingBaseline={loadingBaseline}
        loadingRuleBaseline={loadingRuleBaseline}
        loadingReset={loadingReset}
      />

      {/* Error Alert if any */}
      {fetchError && (
        <div className="max-w-7xl mx-auto w-full px-6 pt-4">
          <div className="bg-rose-950/80 border border-rose-700 text-rose-200 text-xs px-4 py-3 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{fetchError}</span>
            </div>
            <button 
              onClick={fetchAllData}
              className="px-2.5 py-1 bg-rose-900 hover:bg-rose-800 rounded font-semibold text-rose-100 transition"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto w-full px-6 py-6 flex-1 space-y-6">
        
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition ${
              activeTab === 'overview'
                ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Overview & 3-Way Comparison
          </button>

          <button
            onClick={() => setActiveTab('payments')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition ${
              activeTab === 'payments'
                ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <ListOrdered className="w-4 h-4" />
            Transactions ({payments.length})
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition ${
              activeTab === 'audit'
                ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            Audit Trail ({auditLogs.length})
          </button>

          <button
            onClick={() => setActiveTab('architecture')}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition ${
              activeTab === 'architecture'
                ? 'bg-sky-600 text-white shadow-md shadow-sky-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            <Cpu className="w-4 h-4" />
            Architecture & Safety Model
          </button>
        </div>

        {/* Tab 1: Overview & Comparison */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <KpiCards overview={overview} comparison={comparison} />
            <ComparisonView comparison={comparison} />

            {/* Quick Distribution Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Failure Reasons Breakdown */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-sky-400" />
                  Failure Code Distribution
                </h4>
                <div className="space-y-2 text-xs">
                  {overview?.error_code_distribution && Object.entries(overview.error_code_distribution).map(([code, count]) => (
                    <div key={code} className="flex items-center justify-between py-1 border-b border-slate-800/60">
                      <span className="font-mono text-slate-300">{code}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 font-semibold">{count} records</span>
                        <div className="w-20 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className="bg-sky-500 h-full rounded-full" 
                            style={{ width: `${(count / (overview?.total_records || 100)) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Routing Breakdown */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  Policy-Authorized Actions Breakdown
                </h4>
                <div className="space-y-2 text-xs">
                  {overview?.action_distribution && Object.entries(overview.action_distribution).map(([action, count]) => (
                    <div key={action} className="flex items-center justify-between py-1 border-b border-slate-800/60">
                      <span className="font-mono text-slate-300">{action}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 font-semibold">{count} records</span>
                        <div className="w-20 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div 
                            className="bg-indigo-500 h-full rounded-full" 
                            style={{ width: `${(count / (overview?.total_records || 100)) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Tab 2: Transactions List */}
        {activeTab === 'payments' && (
          <TransactionTable
            payments={payments}
            onDiagnosePayment={handleDiagnosePayment}
            loadingPaymentId={loadingPaymentId}
          />
        )}

        {/* Tab 3: Audit Trail */}
        {activeTab === 'audit' && (
          <AuditTrail 
            auditLogs={auditLogs} 
            onRefresh={fetchAllData}
          />
        )}

        {/* Tab 4: Architecture & Safety */}
        {activeTab === 'architecture' && (
          <ArchitectureView />
        )}

      </main>

      {/* Interactive Modal for Single Payment Diagnosis */}
      <RecoveryModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        payment={selectedPayment}
        pipelineResult={pipelineResult}
        isProcessing={isModalProcessing}
      />

    </div>
  );
}
