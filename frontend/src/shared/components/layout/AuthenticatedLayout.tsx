import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { ClassificationBanner } from './ClassificationBanner';
import { Sidebar } from './Sidebar';
import { useUiStore } from '../../../stores/uiStore';
import { useQueue } from '../../hooks/useQueue';
import { RefreshCw, X, AlertTriangle, Info, CheckCircle } from 'lucide-react';

export const AuthenticatedLayout: React.FC = () => {
  const { toasts, removeToast } = useUiStore();
  const { queue } = useQueue();
  const navigate = useNavigate();

  // Find if there is an active consolidation job running to display the header banner
  const activeJob = queue.find((j) => j.status === 'running' && j.jobType === 'consolidation');

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-police-gray">
      {/* 1. Secure Banner (Sticky) */}
      <ClassificationBanner />

      {/* 2. Main Workspace Layout */}
      <div className="flex flex-row flex-1 overflow-hidden">
        {/* Collapsible Sidebar */}
        <Sidebar />

        {/* Contents Area */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Active Task Status Bar Notification (UX Section 7.2) */}
          {activeJob && (
            <div className="bg-police-slate text-white border-b border-police-blue/50 px-6 py-2.5 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <RefreshCw size={14} className="animate-spin text-police-light shrink-0" />
                <span className="text-xs font-semibold text-slate-200 truncate">
                  Consolidation running: {activeJob.currentStep || 'Processing items...'}
                </span>
                {/* Progress bar */}
                <div className="hidden sm:block w-32 md:w-64 bg-police-blue/50 h-2 rounded-full overflow-hidden shrink-0">
                  <div
                    className="bg-police-light h-full transition-all duration-300"
                    style={{ width: `${activeJob.progress}%` }}
                  />
                </div>
                <span className="text-[11px] font-bold text-police-light shrink-0">
                  {activeJob.progress}%
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <button
                  onClick={() => navigate('/queue')}
                  className="text-police-light hover:text-white underline font-medium"
                >
                  View Details
                </button>
              </div>
            </div>
          )}

          {/* Core Page Content Outlet */}
          <main className="flex-1 overflow-y-auto p-6 relative">
            <Outlet />
          </main>
        </div>
      </div>

      {/* 3. Floating Premium Toast Panel */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="panel-glass rounded-lg shadow-premium border border-slate-200/50 p-4 flex items-start justify-between gap-3 pointer-events-auto animate-slide-in"
          >
            <div className="flex gap-2.5 items-start">
              {toast.type === 'success' && <CheckCircle size={18} className="text-emerald-600 mt-0.5 shrink-0" />}
              {toast.type === 'error' && <AlertTriangle size={18} className="text-rose-600 mt-0.5 shrink-0" />}
              {toast.type === 'warning' && <AlertTriangle size={18} className="text-amber-600 mt-0.5 shrink-0" />}
              {toast.type === 'info' && <Info size={18} className="text-sky-600 mt-0.5 shrink-0" />}
              <p className="text-sm font-medium text-slate-800">{toast.message}</p>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-slate-600 p-0.5 rounded transition-colors"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
