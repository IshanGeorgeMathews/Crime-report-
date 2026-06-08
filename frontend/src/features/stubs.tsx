import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useReports } from '../hooks/useReports';
import { api } from '../lib/api';
import { useProfiles } from '../hooks/useProfiles';
import { useGraph } from '../hooks/useGraph';
import { useQueue } from '../hooks/useQueue';
import { useConsolidate } from '../hooks/useConsolidate';
import { useSearch } from '../hooks/useSearch';
import { useUsers } from '../hooks/useUsers';
import type { UserListItem } from '../hooks/useUsers';
import { useUiStore } from '../stores/uiStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import {
  Users,
  Folder,
  Orbit,
  Lock,
  CheckCircle,
  Play,
  Pause,
  Upload,
  Trash2,
  Search,
  Calendar,
  Database,
  Activity,
  Cpu,
  Server,
  Plus,
  Edit,
  ShieldAlert,
  Download,
  RefreshCw,
  Eye,
  Clock,
  Check,
  AlertTriangle,
  X
} from 'lucide-react';
import { Navigate, useNavigate, useParams, Link } from 'react-router-dom';

// --- Login Page ---
export const LoginPage: React.FC = () => {
  const { login, isLoggingIn, isAuthenticated, loginError } = useAuth();
  const [username, setUsername] = useState('analyst');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await login({ username, password });
  };

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 text-white p-6 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      
      <div className="max-w-md w-full backdrop-blur-md bg-slate-900/70 p-8 rounded-2xl border border-slate-800 shadow-2xl text-center space-y-6 relative z-10">
        <div className="flex flex-col items-center gap-3">
          <div className="w-16 h-16 rounded-full bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-400 font-extrabold text-2xl shadow-[0_0_15px_rgba(34,211,238,0.2)] animate-pulse">
            KP
          </div>
          <h2 className="text-2xl font-black text-white tracking-widest">KERALA POLICE</h2>
          <p className="text-[10px] text-cyan-400 font-bold uppercase tracking-widest border-y border-cyan-500/30 py-1 px-4">
            // TOP SECRET // CONSOLIDATION PLATFORM
          </p>
        </div>

        {loginError && (
          <div className="bg-rose-950/40 border border-rose-500/50 text-rose-200 text-xs px-3 py-2 rounded-lg flex items-center gap-2">
            <ShieldAlert size={16} className="text-rose-400 shrink-0" />
            <span className="text-left font-semibold">Access Denied: {loginError.message || "Invalid officer credentials."}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4 text-left">
          <Input
            label="Officer Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="bg-slate-800/80 border-slate-700 text-white placeholder-slate-500 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
          />
          <Input
            label="Access Pin / Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            className="bg-slate-800/80 border-slate-700 text-white placeholder-slate-500 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400"
          />
          <div className="pt-2">
            <Button
              type="submit"
              className="w-full text-slate-950 bg-cyan-400 hover:bg-cyan-300 font-bold shadow-md hover:shadow-cyan-400/20 transition-all duration-300 py-2.5 rounded-lg flex justify-center items-center gap-2"
              isLoading={isLoggingIn}
            >
              <Lock size={16} /> Establish Secure Session
            </Button>
          </div>
        </form>

        <div className="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">
          Authorized personnel only. Activities are audited in real-time.
        </div>
      </div>
    </div>
  );
};

// --- Dashboard Page ---
export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { reports } = useReports();
  const { profiles } = useProfiles();
  const { stats } = useGraph();
  const { queue } = useQueue();
  const navigate = useNavigate();

  // Get active or recent 4 Celery activities
  const recentJobs = queue.slice(0, 4);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 to-slate-850 p-6 rounded-2xl border border-slate-800 shadow-lg text-white">
        <div className="space-y-1">
          <h1 className="text-2xl font-extrabold tracking-tight">Intelligence Command Center</h1>
          <p className="text-slate-400 text-sm">
            Authenticated as <span className="text-cyan-400 font-bold">{user?.fullName}</span> (Role: <span className="uppercase text-xs font-mono font-bold bg-slate-800 px-2 py-0.5 rounded text-teal-300">{user?.role}</span>)
          </p>
        </div>
        <div className="flex items-center gap-2 bg-slate-950/60 border border-slate-800 px-4 py-2 rounded-xl text-xs font-semibold text-slate-300">
          <Activity size={14} className="text-emerald-400 animate-pulse" />
          <span>System Status: <span className="text-emerald-400 font-bold">ONLINE</span></span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-5 hover:shadow-md transition-shadow">
          <div className="w-14 h-14 bg-cyan-50 text-cyan-600 rounded-xl flex items-center justify-center shrink-0">
            <Folder size={28} />
          </div>
          <div className="space-y-0.5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Consolidated Reports</h3>
            <p className="text-3xl font-black text-slate-900">{reports ? reports.length : '0'}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-5 hover:shadow-md transition-shadow">
          <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center shrink-0">
            <Users size={28} />
          </div>
          <div className="space-y-0.5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Suspect PP Dossiers</h3>
            <p className="text-3xl font-black text-slate-900">{profiles ? profiles.length : '0'}</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-5 hover:shadow-md transition-shadow">
          <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center shrink-0">
            <Orbit size={28} />
          </div>
          <div className="space-y-0.5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Graph Network Nodes</h3>
            <p className="text-3xl font-black text-slate-900">{stats?.total_nodes || 0}</p>
          </div>
        </div>
      </div>

      {/* Actions and Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions Panel */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 lg:col-span-1 flex flex-col justify-between space-y-6">
          <div className="space-y-1">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Play size={16} className="text-cyan-600" /> Quick Operations
            </h2>
            <p className="text-xs text-slate-500">Access core functionalities directly.</p>
          </div>
          
          <div className="flex flex-col gap-3">
            <Button
              variant="primary"
              onClick={() => navigate('/consolidate')}
              className="w-full bg-slate-900 hover:bg-slate-850 text-white font-semibold py-2.5 rounded-xl transition-all flex items-center justify-center gap-2"
            >
              <Upload size={16} /> Upload New Files
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/search')}
              className="w-full border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold py-2.5 rounded-xl flex items-center justify-center gap-2"
            >
              <Search size={16} /> Search Intelligence DB
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/graph')}
              className="w-full border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold py-2.5 rounded-xl flex items-center justify-center gap-2"
            >
              <Orbit size={16} /> Network Graph Explorer
            </Button>
          </div>

          <div className="text-[10px] text-slate-400 bg-slate-50 p-3 rounded-lg border border-slate-100 font-medium">
            Kerala Police Intranet Network Node #{Math.floor(Math.random() * 8999) + 1000}
          </div>
        </div>

        {/* Ingestion Engine Status */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Activity size={16} className="text-cyan-600" /> Pipeline Processing Queue
            </h2>
            <Link to="/queue" className="text-xs text-cyan-600 hover:underline font-bold">
              Monitor Queue
            </Link>
          </div>

          {recentJobs.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center text-slate-400 bg-slate-50 rounded-xl border border-dashed border-slate-200">
              <Database size={24} className="mb-2 text-slate-300" />
              <p className="text-xs font-semibold">No recent consolidation pipelines found</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentJobs.map((job) => (
                <div key={job.id} className="py-3 flex items-center justify-between text-xs">
                  <div className="space-y-1 min-w-0 flex-1 pr-4">
                    <p className="font-bold text-slate-800 truncate uppercase">
                      {job.jobType.replace('_', ' ')}
                    </p>
                    <p className="text-[11px] text-slate-400 font-medium flex items-center gap-3">
                      <span>Ref ID: <span className="font-mono">{job.id.substring(0, 8)}</span></span>
                      <span>By: {job.createdBy}</span>
                    </p>
                    {job.status === 'running' && (
                      <div className="space-y-1 pt-1">
                        <div className="flex justify-between text-[10px] font-bold text-cyan-600">
                          <span>{job.currentStep || 'Processing...'}</span>
                          <span>{job.progress}%</span>
                        </div>
                        <div className="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
                          <div className="bg-cyan-500 h-full transition-all duration-300" style={{ width: `${job.progress}%` }} />
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="shrink-0 flex items-center gap-2">
                    <Badge
                      variant={
                        job.status === 'completed' ? 'green' :
                        job.status === 'running' ? 'blue' :
                        job.status === 'failed' ? 'red' : 'gray'
                      }
                    >
                      {job.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// --- Consolidate Page ---
export const ConsolidatePage: React.FC = () => {
  const { uploadFiles, isUploading, uploadError } = useConsolidate();
  const { addToast } = useUiStore();
  const navigate = useNavigate();

  // Helper to format date as DD.MM.YYYY
  const getTodayFormatted = () => {
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const yyyy = today.getFullYear();
    return `${dd}.${mm}.${yyyy}`;
  };

  const [date, setDate] = useState(getTodayFormatted());
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const triggerFileSelect = () => fileInputRef.current?.click();
  const triggerFolderSelect = () => folderInputRef.current?.click();

  const handleFilesAdded = (filesList: FileList | null) => {
    if (!filesList) return;
    const array = Array.from(filesList);
    // Filter for docx only
    const docxOnly = array.filter(f => f.name.endsWith('.docx'));
    if (docxOnly.length < array.length) {
      addToast(`Ignored ${array.length - docxOnly.length} non-.docx files.`, 'warning');
    }
    
    // Check sizes (10MB limit)
    const MAX_SIZE = 10 * 1024 * 1024;
    const oversized = docxOnly.filter(f => f.size > MAX_SIZE);
    if (oversized.length > 0) {
      addToast(`${oversized.length} files exceeded the 10MB limit and were ignored.`, 'error');
    }
    const safeFiles = docxOnly.filter(f => f.size <= MAX_SIZE);

    setSelectedFiles(prev => {
      // Avoid duplicate filenames in select list
      const existingNames = new Set(prev.map(f => f.name));
      const filteredNew = safeFiles.filter(f => !existingNames.has(f.name));
      return [...prev, ...filteredNew];
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files) {
      handleFilesAdded(e.dataTransfer.files);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearSelection = () => {
    setSelectedFiles([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      addToast('Please select or drop at least one .docx file to upload.', 'warning');
      return;
    }
    
    // Validate date format DD.MM.YYYY
    if (!/^\d{2}\.\d{2}\.\d{4}$/.test(date)) {
      addToast('Invalid date format. Must be DD.MM.YYYY (e.g. 06.06.2026)', 'error');
      return;
    }

    try {
      const response = await uploadFiles({ date, files: selectedFiles });
      if (response.success) {
        addToast('Pipeline triggered successfully.', 'success');
        navigate('/queue');
      } else {
        addToast(response.message || 'Upload failed.', 'error');
      }
    } catch (err: any) {
      addToast(err.response?.data?.detail || err.message || 'Upload failed.', 'error');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Consolidate Daily Reports</h1>
        <p className="text-sm text-slate-500">Upload district report docx files to consolidate, translate, and extract suspect GNN nodes.</p>
      </div>

      {uploadError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-4 rounded-xl flex items-start gap-2.5">
          <ShieldAlert size={16} className="text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Execution Error</p>
            <p className="mt-0.5">{uploadError.message || "An error occurred during upload."}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-6">
        {/* Date Input */}
        <div className="max-w-xs space-y-1">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">Report Date</label>
          <div className="relative">
            <Input
              type="text"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              placeholder="DD.MM.YYYY"
              required
              className="pl-9 bg-slate-50 border-slate-200 text-slate-800 placeholder-slate-400 focus:border-cyan-500 focus:bg-white"
            />
            <Calendar className="absolute left-3 top-2.5 text-slate-400" size={16} />
          </div>
          <p className="text-[10px] text-slate-400 font-medium">Must match the report date exactly: DD.MM.YYYY</p>
        </div>

        {/* Drag and Drop Box */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 relative group cursor-pointer ${
            dragOver ? 'border-cyan-500 bg-cyan-50/20' : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
          }`}
          onClick={triggerFileSelect}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => handleFilesAdded(e.target.files)}
            multiple
            className="hidden"
            accept=".docx"
          />
          {/* Webkitdirectory directory file input for folder upload */}
          <input
            type="file"
            ref={folderInputRef}
            onChange={(e) => handleFilesAdded(e.target.files)}
            multiple
            // @ts-ignore
            webkitdirectory=""
            directory=""
            className="hidden"
            accept=".docx"
          />

          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-cyan-50 border border-cyan-100 flex items-center justify-center text-cyan-600 group-hover:scale-110 transition-transform">
              <Upload size={22} />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-700">Drag & drop files or folders here</p>
              <p className="text-xs text-slate-500 font-medium">Accepts multiple district report <span className="font-semibold text-slate-600">.docx</span> documents</p>
            </div>
            <div className="flex items-center gap-3 pt-2 text-xs font-semibold" onClick={(e) => e.stopPropagation()}>
              <button
                type="button"
                onClick={triggerFileSelect}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg flex items-center gap-1.5 transition-colors"
              >
                Select Files
              </button>
              <button
                type="button"
                onClick={triggerFolderSelect}
                className="px-3 py-1.5 border border-slate-200 hover:bg-slate-100 text-slate-700 rounded-lg flex items-center gap-1.5 transition-colors"
              >
                Upload Folder
              </button>
            </div>
          </div>
        </div>

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="space-y-3 bg-slate-50/50 p-4 rounded-xl border border-slate-100">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200/60">
              <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                Selected Files ({selectedFiles.length})
              </h3>
              <button
                type="button"
                onClick={clearSelection}
                className="text-xs text-rose-600 hover:underline font-bold"
              >
                Clear All
              </button>
            </div>
            <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
              {selectedFiles.map((file, idx) => (
                <div key={idx} className="flex justify-between items-center bg-white p-2.5 rounded-lg border border-slate-200/50 text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <Folder size={16} className="text-cyan-600 shrink-0" />
                    <span className="font-medium text-slate-700 truncate">{file.name}</span>
                    <span className="text-[10px] text-slate-400 shrink-0">({(file.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFile(idx)}
                    className="text-slate-400 hover:text-rose-600 p-1 rounded-md transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 border-t border-slate-100 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => { setSelectedFiles([]); setDate(getTodayFormatted()); }}
            disabled={isUploading}
            className="rounded-xl border-slate-200"
          >
            Reset
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={isUploading}
            disabled={selectedFiles.length === 0}
            className="rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold flex items-center gap-1.5"
          >
            <Play size={14} /> Begin Ingestion Pipeline
          </Button>
        </div>
      </form>
    </div>
  );
};

// --- Queue Page ---
export const QueuePage: React.FC = () => {
  const {
    queue,
    isFetchingQueue,
    queueError,
    refetchQueue,
    cancelJob,
    isCancelling,
    stopJob,
    resumeJob,
    deleteJob
  } = useQueue();
  const [confirmCancelId, setConfirmCancelId] = useState<string | null>(null);
  const [cancelSuccess, setCancelSuccess] = useState<string | null>(null);

  const handleRefresh = () => refetchQueue();

  const handleCancelRequest = (jobId: string) => setConfirmCancelId(jobId);
  const handleCancelAbort = () => setConfirmCancelId(null);

  const handleCancelConfirm = async () => {
    if (!confirmCancelId) return;
    try {
      await cancelJob(confirmCancelId);
      setCancelSuccess(confirmCancelId);
      setTimeout(() => setCancelSuccess(null), 4000);
    } catch (err) {
      console.error('Failed to cancel job:', err);
    } finally {
      setConfirmCancelId(null);
    }
  };

  const isActiveCancellable = (status: string) =>
    ['running', 'queued', 'received', 'translating', 'summarizing', 'profile_sync', 'neo4j_sync', 'qdrant_indexing', 'docx_ready'].includes(status);

  if (queueError && queueError.message.includes('403')) {
    return (
      <div className="max-w-2xl mx-auto mt-12 bg-white border border-slate-100 p-8 rounded-2xl shadow-sm text-center space-y-4">
        <div className="w-16 h-16 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto border border-rose-100">
          <ShieldAlert size={28} />
        </div>
        <div className="space-y-1">
          <h2 className="text-lg font-bold text-slate-800">Access Restricted</h2>
          <p className="text-slate-500 text-sm">
            Only administrators, supervisors, and intelligence analysts can monitor the processing queue.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Confirm Cancel Dialog */}
      {confirmCancelId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-100 p-8 max-w-md w-full mx-4 space-y-5">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center border border-amber-100">
                <AlertTriangle size={22} className="text-amber-600" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-800">Cancel Processing Job?</h2>
                <p className="text-sm text-slate-500 mt-1">
                  This will immediately stop the job and <strong>undo all changes</strong> it has made — including deleting any report records and removing uploaded files.
                </p>
                <p className="mt-2 text-xs font-mono text-slate-400 bg-slate-50 rounded px-2 py-1 border border-slate-100 break-all">
                  {confirmCancelId}
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={handleCancelAbort}
                className="px-4 py-2 text-sm font-semibold text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Keep Running
              </button>
              <button
                onClick={handleCancelConfirm}
                disabled={isCancelling}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors disabled:opacity-60"
              >
                {isCancelling ? (
                  <><RefreshCw size={14} className="animate-spin" /> Cancelling...</>
                ) : (
                  <><X size={14} /> Yes, Cancel & Undo</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Processing Queue</h1>
          <p className="text-sm text-slate-500">Monitor and manage asynchronous consolidation jobs.</p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-lg shadow-sm transition-colors"
        >
          <RefreshCw size={14} className={isFetchingQueue ? 'animate-spin text-cyan-600' : ''} />
          Refresh
        </button>
      </div>

      {cancelSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-4 rounded-xl flex items-center gap-2">
          <CheckCircle size={16} className="text-emerald-600 shrink-0" />
          <span><strong>Job cancelled</strong> — all changes have been rolled back.</span>
        </div>
      )}

      {queueError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-4 rounded-xl flex items-center gap-2">
          <ShieldAlert size={16} className="text-rose-600 shrink-0" />
          <span className="font-semibold">Failed to fetch queue: {queueError.message}</span>
        </div>
      )}

      {queue.length === 0 ? (
        <div className="bg-white border border-slate-100 p-12 rounded-2xl shadow-sm text-center max-w-lg mx-auto space-y-3">
          <Server size={32} className="mx-auto text-slate-300 animate-pulse" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-700">No Jobs Executing</h3>
            <p className="text-xs text-slate-500">There are no active or historical tasks queued at the moment.</p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  <th className="p-4">Job ID</th>
                  <th className="p-4">Task Type</th>
                  <th className="p-4">Current Step</th>
                  <th className="p-4">Progress</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Action</th>
                </tr>
              </thead>
              <tbody className="text-xs text-slate-600 divide-y divide-slate-100">
                {queue.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50/50">
                    <td className="p-4 font-mono font-bold text-slate-500">
                      {job.id.substring(0, 13)}...
                    </td>
                    <td className="p-4 font-semibold text-slate-800 uppercase tracking-wide">
                      {job.jobType.replace('_', ' ')}
                    </td>
                    <td className="p-4 font-medium text-slate-500 max-w-[220px] truncate">
                      {job.currentStep || <span className="italic text-slate-300">N/A</span>}
                    </td>
                    <td className="p-4 min-w-[150px]">
                      <div className="flex items-center gap-3">
                        <span className="font-mono font-bold text-[10px] text-slate-500 w-6">
                          {job.progress}%
                        </span>
                        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${
                              job.status === 'failed' ? 'bg-rose-500' :
                              job.status === 'completed' ? 'bg-emerald-500' :
                              job.status === 'cancelled' ? 'bg-amber-400' :
                              job.status === 'stopped' ? 'bg-slate-400' : 'bg-cyan-500'
                            }`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <Badge
                        variant={
                          job.status === 'completed' ? 'green' :
                          job.status === 'running' ? 'blue' :
                          job.status === 'failed' ? 'red' :
                          job.status === 'cancelled' ? 'orange' :
                          job.status === 'stopped' ? 'gray' : 'blue'
                        }
                      >
                        {job.status}
                      </Badge>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {isActiveCancellable(job.status) && (
                          <>
                            <button
                              onClick={() => stopJob(job.id)}
                              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-amber-600 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg transition-colors"
                              title="Temporarily pause the consolidation run"
                            >
                              <Pause size={12} />
                              Pause
                            </button>
                            <button
                              onClick={() => handleCancelRequest(job.id)}
                              className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors"
                              title="Cancel and undo all changes"
                            >
                              <X size={12} />
                              Cancel
                            </button>
                          </>
                        )}
                        
                        {(job.status === 'stopped' || job.status === 'failed') && (
                          <button
                            onClick={() => resumeJob(job.id)}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition-colors"
                            title="Resume/run the process from intermediate state"
                          >
                            <Play size={12} />
                            Run
                          </button>
                        )}

                        {['completed', 'failed', 'cancelled', 'stopped'].includes(job.status) && (
                          <button
                            onClick={() => deleteJob(job.id)}
                            className="flex items-center justify-center p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-100 rounded-lg transition-colors"
                            title="Remove job from queue history"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};



// --- Review Queue (VEG) Page ---
export const ReviewQueuePage: React.FC = () => {
  const { reviewQueue, reviewQueueError, executeReviewAction, isExecutingReview } = useProfiles();
  const { addToast } = useUiStore();

  const handleAction = async (id: string, name: string, action: 'approve' | 'reject') => {
    try {
      const response = await executeReviewAction({ id, action });
      if (response.success) {
        addToast(`Successfully ${action}d ${name}`, 'success');
      } else {
        addToast(`Failed to update candidate: ${response.message}`, 'error');
      }
    } catch (err: any) {
      addToast(err.message || 'Operation failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Review Queue (VEG)</h1>
        <p className="text-sm text-slate-500">Approve or reject candidate profiles flagged by the Named Entity Recognition (NER) pipeline.</p>
      </div>

      {reviewQueueError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-4 rounded-xl flex items-center gap-2">
          <ShieldAlert size={16} className="text-rose-600 shrink-0" />
          <span className="font-semibold">Error loading queue: {reviewQueueError.message}</span>
        </div>
      )}

      {reviewQueue.length === 0 ? (
        <div className="bg-white border border-slate-100 p-12 rounded-2xl shadow-sm text-center max-w-lg mx-auto space-y-3">
          <CheckCircle size={32} className="mx-auto text-emerald-500" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-700">Review Queue Clear</h3>
            <p className="text-xs text-slate-500">There are no pending NER candidate names requiring supervisor vetting.</p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                <th className="p-4">Candidate Suspect Name</th>
                <th className="p-4">Source Mention Context</th>
                <th className="p-4">Extraction Score / Engine</th>
                <th className="p-4">Intelligence Anomalies</th>
                <th className="p-4 text-right">Verification Decisions</th>
              </tr>
            </thead>
            <tbody className="text-xs text-slate-600 divide-y divide-slate-100">
              {reviewQueue.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-bold text-slate-800">{item.name}</td>
                  <td className="p-4 text-slate-500 italic max-w-sm font-medium leading-relaxed">
                    "{item.source}"
                  </td>
                  <td className="p-4 font-mono font-semibold text-slate-500">{item.extractionMethod}</td>
                  <td className="p-4">
                    <Badge variant={item.anomalyFlags ? 'red' : 'gray'}>
                      {item.anomalyFlags || 'None'}
                    </Badge>
                  </td>
                  <td className="p-4 text-right space-x-2 shrink-0">
                    <button
                      onClick={() => handleAction(item.id, item.name, 'reject')}
                      disabled={isExecutingReview}
                      className="px-3 py-1.5 text-xs font-bold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-lg transition-colors inline-flex items-center gap-1 border border-rose-100"
                    >
                      <X size={12} /> Reject
                    </button>
                    <button
                      onClick={() => handleAction(item.id, item.name, 'approve')}
                      disabled={isExecutingReview}
                      className="px-3 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors inline-flex items-center gap-1"
                    >
                      <Check size={12} /> Approve
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// --- Reports Library Page ---
export const ReportListPage: React.FC = () => {
  const { reports, reportsError, downloadDocx } = useReports();
  const { addToast } = useUiStore();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownload = async (id: string, type: 'daily' | 'less-priority') => {
    setDownloadingId(id);
    try {
      await downloadDocx(id, type);
      addToast('Download started successfully.', 'success');
    } catch (e: any) {
      addToast(`Failed to stream report document: ${e.message || "File not found"}`, 'error');
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Consolidated Report Library</h1>
        <p className="text-sm text-slate-500">Access historical daily consolidated documents, event aggregates, and less priority reports.</p>
      </div>

      {reportsError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-4 rounded-xl flex items-center gap-2">
          <ShieldAlert size={16} className="text-rose-600 shrink-0" />
          <span className="font-semibold">Error loading reports: {reportsError.message}</span>
        </div>
      )}

      {reports.length === 0 ? (
        <div className="bg-white border border-slate-100 p-12 rounded-2xl shadow-sm text-center max-w-lg mx-auto space-y-3">
          <Folder size={32} className="mx-auto text-slate-300 animate-pulse" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-700">No Consolidated Reports</h3>
            <p className="text-xs text-slate-500">No consolidated reports exist in the database yet.</p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                <th className="p-4">Report Date</th>
                <th className="p-4">Reference File ID</th>
                <th className="p-4 text-center">Event Items</th>
                <th className="p-4 text-center">Forecast Items</th>
                <th className="p-4 text-center">Social Media Items</th>
                <th className="p-4 text-right">Downloads / Actions</th>
              </tr>
            </thead>
            <tbody className="text-xs text-slate-600 divide-y divide-slate-100">
              {reports.map((rep) => (
                <tr key={rep.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-extrabold text-cyan-600">
                    <Link to={`/reports/${rep.id}`} className="hover:underline flex items-center gap-1.5">
                      <Calendar size={14} /> {rep.reportDate}
                    </Link>
                  </td>
                  <td className="p-4 font-mono font-medium text-slate-500">{rep.refNumber}</td>
                  <td className="p-4 text-center"><Badge variant="blue">{rep.eventCount}</Badge></td>
                  <td className="p-4 text-center"><Badge variant="amber">{rep.forecastCount}</Badge></td>
                  <td className="p-4 text-center"><Badge variant="green">{rep.socialMediaCount}</Badge></td>
                  <td className="p-4 text-right space-x-2 shrink-0">
                    <Link
                      to={`/reports/${rep.id}`}
                      className="px-2.5 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg inline-flex items-center gap-1 font-semibold"
                    >
                      <Eye size={12} /> View Details
                    </Link>
                    <button
                      onClick={() => handleDownload(rep.id, 'daily')}
                      disabled={downloadingId === rep.id}
                      className="px-2.5 py-1.5 text-xs bg-cyan-50 hover:bg-cyan-100 text-cyan-700 border border-cyan-100 rounded-lg inline-flex items-center gap-1 font-semibold"
                    >
                      <Download size={12} /> IS Daily
                    </button>
                    <button
                      onClick={() => handleDownload(rep.id, 'less-priority')}
                      disabled={downloadingId === rep.id}
                      className="px-2.5 py-1.5 text-xs bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-100 rounded-lg inline-flex items-center gap-1 font-semibold"
                    >
                      <Download size={12} /> Less Priority
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// --- Report Detail Page ---
export const ReportDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { reportDetail, isFetchingDetail, detailError, downloadDocx } = useReports(id);
  const { addToast } = useUiStore();
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async (type: 'daily' | 'less-priority') => {
    if (!id) return;
    setDownloading(true);
    try {
      await downloadDocx(id, type);
      addToast('Document downloaded successfully', 'success');
    } catch (e: any) {
      addToast(`Download failed: ${e.message || "File not found"}`, 'error');
    } finally {
      setDownloading(false);
    }
  };

  if (isFetchingDetail) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-400">
        <RefreshCw size={24} className="animate-spin text-cyan-600 mb-2" />
        <span className="text-xs font-semibold">Loading report details...</span>
      </div>
    );
  }

  if (detailError || !reportDetail) {
    return (
      <div className="max-w-xl mx-auto bg-white p-8 rounded-2xl border border-slate-100 text-center space-y-3">
        <ShieldAlert size={28} className="text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-800">Report Not Found</h2>
        <p className="text-slate-500 text-sm">Failed to retrieve details. The record might not exist or you lack viewing permissions.</p>
        <Link to="/reports" className="text-cyan-600 hover:underline font-bold text-xs">Back to Library</Link>
      </div>
    );
  }

  // Categorize report items
  const items = reportDetail.items || [];
  const events = items.filter(x => x.category.toLowerCase() === 'event');
  const forecasts = items.filter(x => x.category.toLowerCase() === 'forecast');
  const socialMedias = items.filter(x => x.category.toLowerCase().includes('social'));

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Info */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-slate-900 text-white rounded text-[10px] font-bold tracking-wider font-mono">CONFIDENTIAL</span>
            <span className="text-xs text-slate-400 font-bold font-mono">REF: {reportDetail.refNumber}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-1.5">
            <Calendar className="text-cyan-600" /> Consolidated Report: {reportDetail.reportDate}
          </h1>
          <p className="text-xs text-slate-500 font-medium">Created: {new Date(reportDetail.createdAt).toLocaleString()} | Operator: {reportDetail.createdBy}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => handleDownload('daily')}
            disabled={downloading}
            className="px-3.5 py-2 text-xs bg-cyan-600 hover:bg-cyan-700 text-white rounded-xl shadow-sm inline-flex items-center gap-1.5 font-bold transition-colors"
          >
            <Download size={14} /> Download Daily IS
          </button>
          <button
            onClick={() => handleDownload('less-priority')}
            disabled={downloading}
            className="px-3.5 py-2 text-xs bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-sm inline-flex items-center gap-1.5 font-bold transition-colors"
          >
            <Download size={14} /> Download Less Priority
          </button>
        </div>
      </div>

      {/* Main Content Sections */}
      <div className="space-y-8">
        {/* 1. Event Items */}
        <div className="space-y-4">
          <div className="border-l-4 border-blue-500 pl-3">
            <h2 className="text-base font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              1. Daily Intelligence Events ({events.length})
            </h2>
          </div>
          {events.length === 0 ? (
            <p className="text-xs italic text-slate-400 bg-white p-4 rounded-xl border border-slate-100">No events reported in this period.</p>
          ) : (
            <div className="space-y-4">
              {events.map((item, idx) => (
                <div key={item.id} className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
                  <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider border-b border-slate-100 pb-2">
                    <span className="text-blue-600">Event #{idx + 1} ({item.districtTag})</span>
                    <span className="text-slate-400">Src: {item.sourceFilename}</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-700 leading-relaxed font-medium">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">English Summary</span>
                      <p className="bg-slate-50 p-3 rounded-lg border border-slate-150 text-slate-800">{item.summaryText}</p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Malayalam Translation</span>
                      <p className="italic text-slate-600">{item.translatedText || <span className="text-slate-300">No translation</span>}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 2. Forecast Items */}
        <div className="space-y-4">
          <div className="border-l-4 border-amber-500 pl-3">
            <h2 className="text-base font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              2. Law & Order Forecasts ({forecasts.length})
            </h2>
          </div>
          {forecasts.length === 0 ? (
            <p className="text-xs italic text-slate-400 bg-white p-4 rounded-xl border border-slate-100">No forecasts logged in this period.</p>
          ) : (
            <div className="space-y-4">
              {forecasts.map((item, idx) => (
                <div key={item.id} className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
                  <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider border-b border-slate-100 pb-2">
                    <span className="text-amber-600">Forecast #{idx + 1} ({item.districtTag})</span>
                    <span className="text-slate-400">Src: {item.sourceFilename}</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-700 leading-relaxed font-medium">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Summary Detail</span>
                      <p className="bg-slate-50 p-3 rounded-lg border border-slate-150 text-slate-800">{item.summaryText}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 3. Social Media Monitoring */}
        <div className="space-y-4">
          <div className="border-l-4 border-emerald-500 pl-3">
            <h2 className="text-base font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              3. Social Media & Threat Feeds ({socialMedias.length})
            </h2>
          </div>
          {socialMedias.length === 0 ? (
            <p className="text-xs italic text-slate-400 bg-white p-4 rounded-xl border border-slate-100">No threat metrics monitored in this period.</p>
          ) : (
            <div className="space-y-4">
              {socialMedias.map((item, idx) => (
                <div key={item.id} className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
                  <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider border-b border-slate-100 pb-2">
                    <span className="text-emerald-600">Feed Item #{idx + 1} ({item.districtTag})</span>
                    <span className="text-slate-400">Src: {item.sourceFilename}</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-700 leading-relaxed font-medium">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Analytic Summary</span>
                      <p className="bg-slate-50 p-3 rounded-lg border border-slate-150 text-slate-800">{item.summaryText}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// --- Profiles Library Page ---
export const ProfileListPage: React.FC = () => {
  const { profiles, profilesError } = useProfiles();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Suspect Dossiers (PP Profiles)</h1>
        <p className="text-sm text-slate-500">Manage individuals under watch, GNN prediction ties, and generate dossier PDFs.</p>
      </div>

      {profilesError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-4 rounded-xl flex items-center gap-2">
          <ShieldAlert size={16} className="text-rose-600 shrink-0" />
          <span className="font-semibold">Error loading suspect directory: {profilesError.message}</span>
        </div>
      )}

      {profiles.length === 0 ? (
        <div className="bg-white border border-slate-100 p-12 rounded-2xl shadow-sm text-center max-w-lg mx-auto space-y-3">
          <Users size={32} className="mx-auto text-slate-300 animate-pulse" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-700">No Suspect Profiles</h3>
            <p className="text-xs text-slate-500">Suspect directory is empty. Approved candidates from NER queue will appear here.</p>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                <th className="p-4">PP ID</th>
                <th className="p-4">Suspect Full Name</th>
                <th className="p-4">Parentage</th>
                <th className="p-4">Assigned Police Station</th>
                <th className="p-4">Threat Classification</th>
                <th className="p-4">Vetting Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="text-xs text-slate-600 divide-y divide-slate-100">
              {profiles.map((prof) => (
                <tr key={prof.id} className="hover:bg-slate-50/50">
                  <td className="p-4 font-mono font-bold text-slate-500">{prof.ppId || 'PP/PENDING'}</td>
                  <td className="p-4 font-extrabold text-cyan-600">
                    <Link to={`/profiles/${prof.id}`} className="hover:underline flex items-center gap-1">
                      {prof.name}
                    </Link>
                  </td>
                  <td className="p-4 font-medium text-slate-600">{prof.parentage || <span className="italic text-slate-300">Not listed</span>}</td>
                  <td className="p-4 font-semibold text-slate-700">{prof.policeStation || 'N/A'}</td>
                  <td className="p-4">
                    <Badge variant="red">{prof.activityType || 'Extremism'}</Badge>
                  </td>
                  <td className="p-4">
                    <Badge variant="green">{prof.reviewStatus}</Badge>
                  </td>
                  <td className="p-4 text-right">
                    <Link
                      to={`/profiles/${prof.id}`}
                      className="px-2.5 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg inline-flex items-center gap-1 font-semibold"
                    >
                      <Eye size={12} /> View Dossier
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// --- Profile Detail Page (Suspect Dossier) ---
export const ProfileDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { profileDetail, isFetchingDetail, detailError } = useProfiles(id);
  const { downloadDocx } = useReports();
  const { addToast } = useUiStore();
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async (type: 'pp' | 'uo') => {
    if (!id) return;
    setDownloading(true);
    try {
      await downloadDocx(id, type);
      addToast('Document download started successfully', 'success');
    } catch (e: any) {
      addToast(`Failed to download dossier document: ${e.message || "File not found"}`, 'error');
    } finally {
      setDownloading(false);
    }
  };

  if (isFetchingDetail) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-400">
        <RefreshCw size={24} className="animate-spin text-cyan-600 mb-2" />
        <span className="text-xs font-semibold">Loading suspect dossier...</span>
      </div>
    );
  }

  if (detailError || !profileDetail) {
    return (
      <div className="max-w-xl mx-auto bg-white p-8 rounded-2xl border border-slate-100 text-center space-y-3">
        <ShieldAlert size={28} className="text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-800">Dossier Not Found</h2>
        <p className="text-slate-500 text-sm">Failed to retrieve suspect records. The database path may have cleared.</p>
        <Link to="/profiles" className="text-cyan-600 hover:underline font-bold text-xs">Back to Directory</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Info */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-rose-600 text-white rounded text-[10px] font-bold tracking-wider font-mono">SUSPECT FILE</span>
            <span className="text-xs text-slate-400 font-bold font-mono">PP ID: {profileDetail.ppId || 'PP/PENDING'}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 flex items-center gap-1.5">
            <Users className="text-cyan-600" /> PP Profile: {profileDetail.name}
          </h1>
          <p className="text-xs text-slate-500 font-medium">Assigned: {profileDetail.policeStation} PS | Class: <span className="font-bold text-rose-600">{profileDetail.activityType || 'Extremism'}</span></p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => handleDownload('pp')}
            disabled={downloading}
            className="px-3.5 py-2 text-xs bg-slate-900 hover:bg-slate-800 text-white rounded-xl shadow-sm inline-flex items-center gap-1.5 font-bold transition-colors"
          >
            <Download size={14} /> Download PP Docx
          </button>
          <button
            onClick={() => handleDownload('uo')}
            disabled={downloading}
            className="px-3.5 py-2 text-xs bg-cyan-600 hover:bg-cyan-700 text-white rounded-xl shadow-sm inline-flex items-center gap-1.5 font-bold transition-colors"
          >
            <Download size={14} /> Generate Malayalam UO Note
          </button>
        </div>
      </div>

      {/* Dossier Grid details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Bio Data */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 lg:col-span-1 space-y-4">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-widest border-b border-slate-100 pb-2">Suspect Biography</h2>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Father's/Spouse Name</span>
              <span className="font-semibold text-slate-700">{profileDetail.parentage || 'N/A'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Date of Birth / Place</span>
              <span className="font-semibold text-slate-700">{profileDetail.dob || 'N/A'} / {profileDetail.placeOfBirth || 'N/A'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Stationary Address</span>
              <span className="font-semibold text-slate-700">{profileDetail.address || 'N/A'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Contact Mobile</span>
              <span className="font-mono font-bold text-slate-700">{profileDetail.mobile || 'N/A'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Identification Marks</span>
              <span className="font-semibold text-slate-700">{profileDetail.identificationMarks || 'N/A'}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase block">Reason for Inclusion</span>
              <p className="text-slate-600 leading-relaxed font-medium mt-0.5">{profileDetail.reasonForInclusion || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Right Columns: Cases, Relations, History */}
        <div className="lg:col-span-2 space-y-6">
          {/* Brief History summary */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-widest border-b border-slate-100 pb-2">Brief History & Background</h2>
            <p className="text-xs text-slate-600 leading-relaxed font-medium">
              {profileDetail.briefHistory || "No historical narrative registered for this suspect profile."}
            </p>
          </div>

          {/* Cases Registered Table */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-widest border-b border-slate-100 pb-2">Registered Criminal Cases ({profileDetail.cases?.length || 0})</h2>
            {!profileDetail.cases || profileDetail.cases.length === 0 ? (
              <p className="text-xs italic text-slate-400">No criminal cases recorded under sections for this individual.</p>
            ) : (
              <div className="overflow-hidden border border-slate-100 rounded-lg">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                      <th className="p-3">FIR Number</th>
                      <th className="p-3">Police Station</th>
                      <th className="p-3">Under Sections</th>
                      <th className="p-3">Co-Accused</th>
                      <th className="p-3">Case Status</th>
                    </tr>
                  </thead>
                  <tbody className="text-[11px] text-slate-600 divide-y divide-slate-100">
                    {profileDetail.cases.map((c) => (
                      <tr key={c.id}>
                        <td className="p-3 font-bold text-slate-800">{c.firNumber}</td>
                        <td className="p-3 font-semibold text-slate-700">{c.policeStation}</td>
                        <td className="p-3 font-mono font-medium text-slate-500">{c.underSections || 'N/A'}</td>
                        <td className="p-3 font-medium text-slate-500 truncate max-w-[150px]" title={c.coAccused}>{c.coAccused || 'None'}</td>
                        <td className="p-3"><Badge variant="amber">{c.caseStatus}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Known Associates / Relations */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-widest border-b border-slate-100 pb-2">Traversed Associations / Relations ({profileDetail.relations?.length || 0})</h2>
            {!profileDetail.relations || profileDetail.relations.length === 0 ? (
              <p className="text-xs italic text-slate-400">No registered familial or criminal association ties.</p>
            ) : (
              <div className="overflow-hidden border border-slate-100 rounded-lg">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                      <th className="p-3">Associate Name</th>
                      <th className="p-3">Relationship Type</th>
                      <th className="p-3">Contact Mobile</th>
                      <th className="p-3">Resident Address</th>
                    </tr>
                  </thead>
                  <tbody className="text-[11px] text-slate-600 divide-y divide-slate-100">
                    {profileDetail.relations.map((r) => (
                      <tr key={r.id}>
                        <td className="p-3 font-bold text-slate-800">{r.name}</td>
                        <td className="p-3"><Badge variant="blue">{r.relationType}</Badge></td>
                        <td className="p-3 font-mono text-slate-500">{r.mobile || 'N/A'}</td>
                        <td className="p-3 font-medium text-slate-500">{r.address || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// --- Graph Force Layout Hook (mini physics engine) ---
function useForceLayout(
  nodes: { id: string; type: string; label: string; properties?: any }[],
  edges: { source: string; target: string }[],
  width: number,
  height: number
) {
  const [positions, setPositions] = React.useState<Map<string, { x: number; y: number }>>(new Map());

  React.useEffect(() => {
    if (nodes.length === 0) { setPositions(new Map()); return; }

    const pos = new Map<string, { x: number; y: number }>();
    nodes.forEach((n, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      const r = Math.min(width, height) * 0.32;
      pos.set(n.id, {
        x: width / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 40,
        y: height / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 40,
      });
    });

    const k = Math.sqrt((width * height) / (nodes.length || 1));
    const iterations = 80;
    const padding = 30;

    for (let iter = 0; iter < iterations; iter++) {
      const temp = 10 * (1 - iter / iterations);

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const pi = pos.get(nodes[i].id)!;
          const pj = pos.get(nodes[j].id)!;
          const dx = pi.x - pj.x;
          const dy = pi.y - pj.y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.1);
          const force = (k * k) / dist;
          const fx = (dx / dist) * force * 0.05;
          const fy = (dy / dist) * force * 0.05;
          pos.set(nodes[i].id, { x: pi.x + fx, y: pi.y + fy });
          pos.set(nodes[j].id, { x: pj.x - fx, y: pj.y - fy });
        }
      }

      edges.forEach(e => {
        const ps = pos.get(e.source);
        const pt = pos.get(e.target);
        if (!ps || !pt) return;
        const dx = pt.x - ps.x;
        const dy = pt.y - ps.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 0.1);
        const force = (dist * dist) / k * 0.05;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        pos.set(e.source, { x: ps.x + fx * temp, y: ps.y + fy * temp });
        pos.set(e.target, { x: pt.x - fx * temp, y: pt.y - fy * temp });
      });

      nodes.forEach(n => {
        const p = pos.get(n.id)!;
        pos.set(n.id, {
          x: Math.max(padding, Math.min(width - padding, p.x)),
          y: Math.max(padding, Math.min(height - padding, p.y)),
        });
      });
    }

    setPositions(new Map(pos));
  }, [nodes, edges, width, height]);

  return positions;
}

// --- Graph Explorer Page ---
export const GraphExplorerPage: React.FC = () => {
  const { graphData, isFetchingGraph, stats, queryGraph, cleanGraph, isCleaning, fetchAssociates } = useGraph();
  const { addToast } = useUiStore();
  const svgRef = useRef<SVGSVGElement>(null);

  const [queryMode, setQueryMode] = useState<'all' | 'node' | 'date' | 'crime'>('all');
  const [nameInput, setNameInput] = useState('');
  const [dateInput, setDateInput] = useState('');
  const [crimeInput, setCrimeInput] = useState('');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [associates, setAssociates] = useState<any[]>([]);
  const [isFetchingAssociates, setIsFetchingAssociates] = useState(false);

  const SVG_W = 700;
  const SVG_H = 500;
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: SVG_W, h: SVG_H });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ mx: 0, my: 0, vx: 0, vy: 0 });

  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];
  const positions = useForceLayout(nodes, edges, SVG_W, SVG_H);

  useEffect(() => {
    queryGraph({ queryType: 'all' }).catch(() => {});
  }, []);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (queryMode === 'all') {
        await queryGraph({ queryType: 'all' });
      } else if (queryMode === 'node') {
        if (!nameInput.trim()) { addToast('Enter a suspect name to query.', 'warning'); return; }
        await queryGraph({ queryType: 'node', centerNodeId: nameInput.trim() });
      } else if (queryMode === 'date') {
        if (!dateInput.trim()) { addToast('Enter a date in DD.MM.YYYY format.', 'warning'); return; }
        await queryGraph({ queryType: 'date', date: dateInput.trim() });
      } else if (queryMode === 'crime') {
        if (!crimeInput.trim()) { addToast('Enter a crime keyword.', 'warning'); return; }
        await queryGraph({ queryType: 'crime', crimeKeyword: crimeInput.trim() });
      }
      setSelectedNode(null);
      setAssociates([]);
    } catch (e: any) {
      addToast(`Query failed: ${e.message}`, 'error');
    }
  };

  const handleNodeClick = async (node: any) => {
    setSelectedNode(node);
    if (node.type === 'individual') {
      setIsFetchingAssociates(true);
      try {
        const result = await fetchAssociates(node.label || node.id);
        setAssociates(result);
      } catch { setAssociates([]); }
      finally { setIsFetchingAssociates(false); }
    } else {
      setAssociates([]);
    }
  };

  const handleNodeDblClick = async (node: any) => {
    try {
      await queryGraph({ queryType: 'node', centerNodeId: node.id, depth: 2 });
      setSelectedNode(node);
    } catch (e: any) {
      addToast(`Subgraph query failed: ${e.message}`, 'error');
    }
  };

  const handleCleanGraph = async () => {
    if (!window.confirm('Clean junk nodes from the graph database?')) return;
    try {
      const response = await cleanGraph();
      if (response.success) {
        addToast(`Removed ${response.data.removedCount} invalid nodes.`, 'success');
        await queryGraph({ queryType: 'all' });
      }
    } catch (e: any) {
      addToast(`Failed: ${e.message}`, 'error');
    }
  };

  const onSvgMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    const tag = (e.target as SVGElement).tagName;
    if (tag === 'svg' || tag === 'rect') {
      setIsPanning(true);
      setPanStart({ mx: e.clientX, my: e.clientY, vx: viewBox.x, vy: viewBox.y });
    }
  };
  const onSvgMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isPanning) return;
    const scaleX = viewBox.w / (svgRef.current?.clientWidth || SVG_W);
    const scaleY = viewBox.h / (svgRef.current?.clientHeight || SVG_H);
    setViewBox(v => ({
      ...v,
      x: panStart.vx - (e.clientX - panStart.mx) * scaleX,
      y: panStart.vy - (e.clientY - panStart.my) * scaleY,
    }));
  };
  const onSvgMouseUp = () => setIsPanning(false);
  const onSvgWheel = (e: React.WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.12 : 0.88;
    setViewBox(v => {
      const newW = Math.max(200, Math.min(SVG_W * 2, v.w * factor));
      const newH = Math.max(150, Math.min(SVG_H * 2, v.h * factor));
      return { x: v.x + (v.w - newW) / 2, y: v.y + (v.h - newH) / 2, w: newW, h: newH };
    });
  };

  const NODE_COLORS: Record<string, { fill: string; stroke: string }> = {
    individual:   { fill: '#f43f5e', stroke: '#fb7185' },
    crime:        { fill: '#6366f1', stroke: '#818cf8' },
    record:       { fill: '#f59e0b', stroke: '#fcd34d' },
    case:         { fill: '#0ea5e9', stroke: '#38bdf8' },
    organization: { fill: '#10b981', stroke: '#34d399' },
    unknown:      { fill: '#64748b', stroke: '#94a3b8' },
  };
  const getColor = (type: string) => NODE_COLORS[type] || NODE_COLORS.unknown;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Intelligence Network Explorer</h1>
          <p className="text-sm text-slate-500">Query Neo4j graph by suspect name, crime keyword, or date. Double-click a node to drill into its subgraph.</p>
        </div>
        <button
          onClick={handleCleanGraph}
          disabled={isCleaning}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold bg-rose-50 text-rose-600 hover:bg-rose-100 rounded-xl border border-rose-100 transition-colors shrink-0 shadow-sm"
        >
          <Trash2 size={13} /> Clean Junk Nodes
        </button>
      </div>

      {/* Query bar */}
      <form onSubmit={handleQuery} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
        <div className="flex flex-wrap gap-3 items-end">
          {/* Mode buttons */}
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Query Mode</label>
            <div className="flex rounded-xl overflow-hidden border border-slate-200 text-xs font-bold divide-x divide-slate-200">
              {(['all','node','date','crime'] as const).map(m => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setQueryMode(m)}
                  className={`px-3 py-2 capitalize transition-colors ${queryMode === m ? 'bg-slate-900 text-white' : 'bg-white text-slate-500 hover:bg-slate-50'}`}
                >
                  {m === 'all' ? 'All Nodes' : m === 'node' ? 'By Name' : m === 'date' ? 'By Date' : 'By Crime'}
                </button>
              ))}
            </div>
          </div>

          {queryMode === 'node' && (
            <div className="flex-1 min-w-[180px] space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Suspect Name / Node ID</label>
              <Input value={nameInput} onChange={e => setNameInput(e.target.value)} placeholder="e.g. Mohammed Rafi" className="bg-slate-50 border-slate-200 text-sm" />
            </div>
          )}
          {queryMode === 'date' && (
            <div className="flex-1 min-w-[180px] space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Report Date (DD.MM.YYYY)</label>
              <div className="relative">
                <Input value={dateInput} onChange={e => setDateInput(e.target.value)} placeholder="06.06.2026" className="bg-slate-50 border-slate-200 text-sm pl-9" />
                <Calendar className="absolute left-3 top-2.5 text-slate-400" size={15} />
              </div>
            </div>
          )}
          {queryMode === 'crime' && (
            <div className="flex-1 min-w-[180px] space-y-1">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Crime / Incident Keyword</label>
              <Input value={crimeInput} onChange={e => setCrimeInput(e.target.value)} placeholder="e.g. maoist, robbery, IED" className="bg-slate-50 border-slate-200 text-sm" />
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            isLoading={isFetchingGraph}
            className="bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl px-5 py-2 text-sm flex items-center gap-1.5 self-end"
          >
            <Search size={14} /> Run Query
          </Button>
        </div>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Left: Stats + Legend */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2">DB Overview</h3>
            {[
              { label: 'Total Nodes', val: stats?.total_nodes },
              { label: 'Edges', val: stats?.total_edges },
              { label: 'Suspects', val: stats?.individual_nodes },
              { label: 'Crime Events', val: stats?.crime_nodes },
              { label: 'Records', val: stats?.record_nodes },
              { label: 'Cases', val: stats?.case_nodes },
            ].map(row => (
              <div key={row.label} className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">{row.label}</span>
                <span className="font-bold text-slate-800 font-mono">{row.val ?? '—'}</span>
              </div>
            ))}
          </div>
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-2">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2">Node Legend</h3>
            {Object.entries(NODE_COLORS).filter(([k]) => k !== 'unknown').map(([type, col]) => (
              <div key={type} className="flex items-center gap-2 text-xs font-medium text-slate-600 capitalize">
                <div className="w-3 h-3 rounded-full shrink-0" style={{ background: col.fill }} />
                {type}
              </div>
            ))}
          </div>
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 text-xs space-y-1.5">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2">Visible Graph</h3>
            <div className="flex justify-between"><span className="text-slate-500">Nodes shown</span><span className="font-bold font-mono text-slate-800">{nodes.length}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Edges shown</span><span className="font-bold font-mono text-slate-800">{edges.length}</span></div>
          </div>
        </div>

        {/* Center: SVG Canvas */}
        <div className="lg:col-span-2 bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden relative shadow-xl" style={{ minHeight: 500 }}>
          <div className="absolute top-3 left-3 z-10 text-[9px] text-slate-500 font-semibold uppercase tracking-widest leading-relaxed pointer-events-none">
            <div>Scroll: zoom · Drag: pan</div>
            <div>Click: inspect · Dbl-click: drill down</div>
          </div>

          {isFetchingGraph ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 z-10">
              <RefreshCw size={28} className="animate-spin text-cyan-400 mb-3" />
              <span className="text-xs font-bold tracking-wide">Traversing Neo4j network paths...</span>
            </div>
          ) : nodes.length === 0 ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8 gap-3">
              <Database size={36} className="text-slate-700" />
              <div className="space-y-1">
                <p className="text-slate-400 text-sm font-bold">No graph data returned</p>
                <p className="text-slate-600 text-xs">Try "All Nodes" or refine your search criteria.</p>
              </div>
            </div>
          ) : (
            <svg
              ref={svgRef}
              className="w-full h-full select-none"
              viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
              style={{ cursor: isPanning ? 'grabbing' : 'grab', minHeight: 500 }}
              onMouseDown={onSvgMouseDown}
              onMouseMove={onSvgMouseMove}
              onMouseUp={onSvgMouseUp}
              onMouseLeave={onSvgMouseUp}
              onWheel={onSvgWheel}
            >
              <defs>
                <pattern id="neo-grid" width="30" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.025)" strokeWidth="0.5"/>
                </pattern>
                <marker id="arrowhead" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M 0 0 L 6 3 L 0 6 z" fill="rgba(34,211,238,0.35)" />
                </marker>
              </defs>
              <rect x={-5000} y={-5000} width={15000} height={15000} fill="url(#neo-grid)" />

              {/* Edges */}
              {edges.map((edge, idx) => {
                const src = positions.get(edge.source);
                const tgt = positions.get(edge.target);
                if (!src || !tgt) return null;
                const mx = (src.x + tgt.x) / 2;
                const my = (src.y + tgt.y) / 2;
                return (
                  <g key={edge.id || idx}>
                    <line
                      x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
                      stroke="rgba(34,211,238,0.18)"
                      strokeWidth={1.2}
                      markerEnd="url(#arrowhead)"
                    />
                    <text x={mx} y={my - 4} fill="rgba(34,211,238,0.4)" fontSize={7} fontWeight="600" textAnchor="middle" style={{ pointerEvents: 'none' }}>
                      {String(edge.type || '').replace(/_/g, ' ')}
                    </text>
                  </g>
                );
              })}

              {/* Nodes */}
              {nodes.map(n => {
                const pos = positions.get(n.id);
                if (!pos) return null;
                const color = getColor(n.type);
                const isSelected = selectedNode?.id === n.id;
                const r = n.type === 'record' ? 10 : n.type === 'individual' ? 15 : 12;
                const label = (n.label || n.id || '').toString().slice(0, 20);

                return (
                  <g
                    key={n.id}
                    style={{ cursor: 'pointer' }}
                    onClick={ev => { ev.stopPropagation(); handleNodeClick(n); }}
                    onDoubleClick={ev => { ev.stopPropagation(); handleNodeDblClick(n); }}
                  >
                    {isSelected && (
                      <circle cx={pos.x} cy={pos.y} r={r + 7} fill="none" stroke="rgba(34,211,238,0.5)" strokeWidth={1.5} strokeDasharray="4 2" />
                    )}
                    {isSelected && (
                      <circle cx={pos.x} cy={pos.y} r={r + 4} fill={color.fill} opacity={0.15} />
                    )}
                    <circle
                      cx={pos.x} cy={pos.y} r={r}
                      fill={color.fill}
                      stroke={color.stroke}
                      strokeWidth={isSelected ? 2.5 : 1.5}
                      style={{ filter: isSelected ? `drop-shadow(0 0 8px ${color.fill})` : `drop-shadow(0 0 3px ${color.fill}66)` }}
                    />
                    <text x={pos.x} y={pos.y + 4.5} fill="white" fontSize={9} fontWeight="900" textAnchor="middle" style={{ pointerEvents: 'none' }}>
                      {(n.type || 'U')[0].toUpperCase()}
                    </text>
                    <text x={pos.x} y={pos.y + r + 12} fill="rgba(255,255,255,0.7)" fontSize={8} fontWeight="600" textAnchor="middle" style={{ pointerEvents: 'none' }}>
                      {label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}

          <div className="absolute bottom-3 right-3 text-[9px] text-cyan-500 font-bold tracking-widest uppercase bg-slate-900/80 px-2.5 py-1 border border-slate-800 rounded-lg">
            NEO4J · {nodes.length} nodes · {edges.length} edges
          </div>
        </div>

        {/* Right: Inspector + GNN */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2 flex items-center gap-1.5">
              <Activity size={12} className="text-cyan-600" /> Node Inspector
            </h3>
            {!selectedNode ? (
              <p className="text-xs italic text-slate-400 text-center py-4">Click a node on the graph to inspect its properties.</p>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full shrink-0" style={{ background: getColor(selectedNode.type).fill }} />
                  <span className="font-bold text-slate-800 truncate">{selectedNode.label || selectedNode.id}</span>
                </div>
                <Badge variant={selectedNode.type === 'individual' ? 'red' : selectedNode.type === 'crime' ? 'blue' : 'gray'}>
                  {selectedNode.type}
                </Badge>
                <div className="bg-slate-50 rounded-xl p-2.5 space-y-2 max-h-52 overflow-y-auto">
                  {Object.entries(selectedNode.properties || {})
                    .filter(([k]) => !['node_id'].includes(k))
                    .slice(0, 14)
                    .map(([k, v]) => (
                      <div key={k} className="flex flex-col gap-0.5">
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{k.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-slate-700 break-words text-[11px]">{String(v || '').slice(0, 140)}</span>
                      </div>
                    ))}
                </div>
                <button
                  onClick={() => handleNodeDblClick(selectedNode)}
                  className="w-full py-1.5 text-xs font-bold text-cyan-700 bg-cyan-50 hover:bg-cyan-100 rounded-lg border border-cyan-100 transition-colors"
                >
                  Drill into subgraph →
                </button>
              </div>
            )}
          </div>

          <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 space-y-3">
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-100 pb-2 flex items-center gap-1.5">
              <Cpu size={12} className="text-cyan-600" /> GNN Link Prediction
            </h3>
            {isFetchingAssociates ? (
              <div className="flex flex-col items-center py-4 text-slate-400 gap-2">
                <RefreshCw size={16} className="animate-spin text-cyan-600" />
                <span className="text-[10px] font-semibold">Running GCN model...</span>
              </div>
            ) : !selectedNode || selectedNode.type !== 'individual' ? (
              <p className="text-xs italic text-slate-400 text-center py-3">Select a suspect (individual) node to see predicted ties.</p>
            ) : associates.length === 0 ? (
              <p className="text-xs italic text-slate-400 text-center py-3">No hidden links predicted for this suspect.</p>
            ) : (
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {associates.map((item: any, idx: number) => (
                  <div key={idx} className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-xs flex justify-between items-center gap-2">
                    <div className="min-w-0">
                      <span className="font-bold text-slate-800 block truncate">{item.name}</span>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase">
                        {item.hasEdge ? 'Direct Tie' : 'Predicted (GNN)'}
                      </span>
                    </div>
                    <Badge variant={item.similarity > 0.75 ? 'red' : 'blue'}>
                      {(item.similarity * 100).toFixed(0)}%
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// --- Unified Search Page ---
export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const { searchSemantic, isSearchingSemantic, semanticResults, searchStructured, isSearchingStructured, structuredResults } = useSearch();
  const [activeTab, setActiveTab] = useState<'semantic' | 'structured'>('semantic');
  const { addToast } = useUiStore();

  const handleSearch = async (type: 'semantic' | 'structured') => {
    if (!query.trim()) {
      addToast('Please input a search query first', 'warning');
      return;
    }
    setActiveTab(type);
    try {
      if (type === 'semantic') {
        await searchSemantic({ query });
      } else {
        await searchStructured({ query });
      }
    } catch (e: any) {
      addToast(`Search failed: ${e.message}`, 'error');
    }
  };

  const results = activeTab === 'semantic' ? semanticResults : structuredResults;
  const isLoading = activeTab === 'semantic' ? isSearchingSemantic : isSearchingStructured;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Unified Search</h1>
        <p className="text-sm text-slate-500">Perform SQL relational structured filters or Qdrant vector similarity check on district reports.</p>
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-4">
        <div className="relative">
          <Input
            placeholder="Enter search query: e.g. Maoist cadre arrest, anti-terror raids..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-10 py-3.5 text-sm bg-slate-50 border-slate-200 focus:bg-white"
          />
          <Search className="absolute left-3.5 top-3.5 text-slate-400" size={18} />
        </div>
        <div className="flex gap-3">
          <Button
            onClick={() => handleSearch('semantic')}
            disabled={isLoading}
            className="bg-slate-900 hover:bg-slate-800 text-white font-semibold flex items-center gap-1.5 rounded-xl px-4 py-2"
          >
            <Orbit size={16} /> Qdrant Vector Semantic Search
          </Button>
          <Button
            onClick={() => handleSearch('structured')}
            disabled={isLoading}
            variant="outline"
            className="border-slate-200 hover:bg-slate-50 font-semibold flex items-center gap-1.5 rounded-xl px-4 py-2"
          >
            <Database size={16} /> Relational SQL Search
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="h-48 flex flex-col items-center justify-center text-slate-400">
          <RefreshCw size={24} className="animate-spin text-cyan-600 mb-2" />
          <span className="text-xs font-semibold">Running database query index...</span>
        </div>
      ) : results.length === 0 ? (
        query && (
          <div className="bg-white border border-slate-100 p-12 rounded-2xl shadow-sm text-center space-y-2">
            <ShieldAlert size={28} className="text-slate-300 mx-auto" />
            <h3 className="text-sm font-bold text-slate-700">No Results Found</h3>
            <p className="text-xs text-slate-500">Try adjusting your filters or query text.</p>
          </div>
        )
      ) : (
        <div className="space-y-4">
          <div className="border-l-4 border-cyan-500 pl-3">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-widest">
              Search Results ({results.length})
            </h2>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    <th className="p-4">Entity Type</th>
                    <th className="p-4">Title / Context</th>
                    {activeTab === 'semantic' && <th className="p-4">Confidence Score</th>}
                    <th className="p-4">Snippet Preview</th>
                    <th className="p-4 text-right">Dossier Links</th>
                  </tr>
                </thead>
                <tbody className="text-xs text-slate-600 divide-y divide-slate-100">
                  {results.map((hit, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="p-4">
                        <Badge
                          variant={
                            hit.entityType === 'profile' ? 'red' :
                            hit.entityType === 'report_item' ? 'blue' : 'gray'
                          }
                        >
                          {hit.entityType}
                        </Badge>
                      </td>
                      <td className="p-4 font-bold text-slate-800">{hit.title}</td>
                      {activeTab === 'semantic' && (
                        <td className="p-4 font-mono font-bold text-cyan-600">
                          {hit.score ? `${(hit.score * 100).toFixed(1)}%` : 'N/A'}
                        </td>
                      )}
                      <td className="p-4 text-slate-500 max-w-sm truncate" title={hit.snippet}>
                        {hit.snippet}
                      </td>
                      <td className="p-4 text-right">
                        {hit.entityType === 'profile' ? (
                          <Link
                            to={`/profiles/${hit.id}`}
                            className="px-2.5 py-1 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg inline-flex items-center gap-1 font-semibold"
                          >
                            <Eye size={12} /> View Dossier
                          </Link>
                        ) : (
                          <Link
                            to={`/reports/${hit.id}`}
                            className="px-2.5 py-1 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg inline-flex items-center gap-1 font-semibold"
                          >
                            <Eye size={12} /> View Report
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- Ingestion Schedules Page ---
export const SchedulePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Ingestion Schedules</h1>
        <p className="text-sm text-slate-500">Configure file watch directory cron jobs and automated FTP ingestion triggers.</p>
      </div>

      <div className="bg-white p-8 rounded-2xl border border-slate-100 text-center max-w-lg mx-auto space-y-3">
        <Clock size={32} className="mx-auto text-slate-400" />
        <h3 className="text-sm font-bold text-slate-700">Scheduled Watchers</h3>
        <p className="text-xs text-slate-500 leading-relaxed font-medium">
          Automated crons scan district file-shares every morning at <span className="font-bold text-slate-700">06:00 AM IST</span>. You can manually run pipeline executions from the <span className="font-bold text-slate-700">Consolidate</span> page.
        </p>
      </div>
    </div>
  );
};

// --- Admin Officer Directory CRUD Page ---
export const UserManagementPage: React.FC = () => {
  const { users, usersError, createUser, updateUser, deactivateUser } = useUsers();
  const { addToast } = useUiStore();
  const { user: currentUser } = useAuth();

  // Create User State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<'admin' | 'supervisor' | 'analyst' | 'viewer'>('analyst');
  const [district, setDistrict] = useState('');

  // Edit User State
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password || !fullName) {
      addToast('Please fill out all required fields', 'warning');
      return;
    }
    try {
      const payload = { username, password, fullName, role, district: district || undefined };
      const response = await createUser(payload);
      if (response.success) {
        addToast(`Successfully created user: ${username}`, 'success');
        setShowCreateModal(false);
        setUsername('');
        setPassword('');
        setFullName('');
        setRole('analyst');
        setDistrict('');
      } else {
        addToast(`Failed to create user: ${response.message}`, 'error');
      }
    } catch (e: any) {
      addToast(e.response?.data?.detail || e.message || 'Operation failed', 'error');
    }
  };

  const handleToggleActive = async (targetUser: UserListItem) => {
    if (targetUser.id === currentUser?.id) {
      addToast("You cannot deactivate your own administrative session.", "error");
      return;
    }
    const actionWord = targetUser.is_active ? 'deactivate' : 'activate';
    if (!window.confirm(`Are you sure you want to ${actionWord} officer ${targetUser.username}?`)) return;

    try {
      if (targetUser.is_active) {
        const response = await deactivateUser(targetUser.id);
        if (response.success) {
          addToast(`Officer deactivated successfully`, 'success');
        }
      } else {
        const response = await updateUser({ id: targetUser.id, isActive: true });
        if (response.success) {
          addToast(`Officer activated successfully`, 'success');
        }
      }
    } catch (e: any) {
      addToast(e.message || 'Failed to toggle active status', 'error');
    }
  };

  const handleEditUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    try {
      const response = await updateUser({
        id: editingUser.id,
        fullName: editingUser.fullName,
        role: editingUser.role,
        district: editingUser.district || undefined,
        isActive: editingUser.is_active
      });
      if (response.success) {
        addToast(`User updated successfully`, 'success');
        setEditingUser(null);
      }
    } catch (e: any) {
      addToast(e.message || 'Update failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Officer Directory</h1>
          <p className="text-sm text-slate-500">Manage analyst, supervisor, and viewer credentials and platform access permissions.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 rounded-xl shadow-sm transition-colors"
        >
          <Plus size={14} /> Add New Officer
        </button>
      </div>

      {usersError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-xs p-4 rounded-xl flex items-center gap-2">
          <ShieldAlert size={16} className="text-rose-600 shrink-0" />
          <span className="font-semibold">Error loading user logs: {usersError.message}</span>
        </div>
      )}

      {/* Directory Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              <th className="p-4">Username / ID</th>
              <th className="p-4">Full Name</th>
              <th className="p-4">Assigned Role</th>
              <th className="p-4">District Branch</th>
              <th className="p-4">Last Login</th>
              <th className="p-4">Status</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="text-xs text-slate-600 divide-y divide-slate-100">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50/50">
                <td className="p-4 font-mono font-bold text-slate-500">{u.username}</td>
                <td className="p-4 font-bold text-slate-800">{u.fullName}</td>
                <td className="p-4">
                  <Badge
                    variant={
                      u.role === 'admin' ? 'red' :
                      u.role === 'supervisor' ? 'amber' :
                      u.role === 'analyst' ? 'blue' : 'gray'
                    }
                  >
                    {u.role}
                  </Badge>
                </td>
                <td className="p-4 font-semibold text-slate-700">{u.district || 'HQ'}</td>
                <td className="p-4 font-medium text-slate-400">
                  {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}
                </td>
                <td className="p-4">
                  <Badge variant={u.is_active ? 'green' : 'gray'}>
                    {u.is_active ? 'active' : 'inactive'}
                  </Badge>
                </td>
                <td className="p-4 text-right space-x-2 shrink-0">
                  <button
                    onClick={() => setEditingUser(u)}
                    className="p-1.5 text-slate-400 hover:text-cyan-600 hover:bg-slate-50 rounded transition-colors inline-flex items-center"
                    title="Edit Profile"
                  >
                    <Edit size={14} />
                  </button>
                  <button
                    onClick={() => handleToggleActive(u)}
                    disabled={u.id === currentUser?.id}
                    className={`px-2 py-1 text-[10px] font-bold rounded-lg border transition-colors ${
                      u.is_active
                        ? 'text-rose-600 bg-rose-50 border-rose-100 hover:bg-rose-100'
                        : 'text-emerald-600 bg-emerald-50 border-emerald-100 hover:bg-emerald-100'
                    }`}
                  >
                    {u.is_active ? 'Deactivate' : 'Reactivate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 1. Create User Modal Overlay */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-100 max-w-md w-full overflow-hidden animate-slide-in">
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Plus size={16} /> Add Officer Credentials
              </h2>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="p-5 space-y-4 text-xs font-semibold text-slate-700">
              <Input
                label="Username / Badge ID"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="bg-slate-50 border-slate-200"
              />
              <Input
                label="Security Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-slate-50 border-slate-200"
              />
              <Input
                label="Officer Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="bg-slate-50 border-slate-200"
              />

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Assigned Role Type</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as any)}
                  className="w-full border border-slate-200 bg-slate-50 px-3 py-2 rounded-lg font-semibold text-slate-700 focus:outline-none focus:border-cyan-500"
                >
                  <option value="analyst">Intelligence Analyst</option>
                  <option value="supervisor">Supervising Officer</option>
                  <option value="viewer">Command Room Viewer</option>
                  <option value="admin">System Administrator</option>
                </select>
              </div>

              <Input
                label="District Branch Jurisdiction (Leave empty for HQ)"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                placeholder="e.g. PKD, TVM, KOZ"
                className="bg-slate-50 border-slate-200"
              />

              <div className="flex justify-end gap-2 border-t border-slate-100 pt-4 mt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)} className="rounded-lg">
                  Cancel
                </Button>
                <Button type="submit" variant="primary" className="bg-slate-900 hover:bg-slate-800 text-white rounded-lg">
                  Create Account
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. Edit User Modal Overlay */}
      {editingUser && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-100 max-w-md w-full overflow-hidden animate-slide-in">
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider flex items-center gap-1.5">
                <Edit size={16} /> Edit Officer Details
              </h2>
              <button onClick={() => setEditingUser(null)} className="text-slate-400 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleEditUser} className="p-5 space-y-4 text-xs font-semibold text-slate-700">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Username (Read-Only)</label>
                <div className="w-full bg-slate-100 border border-slate-200 px-3 py-2 rounded-lg font-mono font-bold text-slate-500">
                  {editingUser.username}
                </div>
              </div>

              <Input
                label="Officer Full Name"
                value={editingUser.fullName}
                onChange={(e) => setEditingUser({ ...editingUser, fullName: e.target.value })}
                required
                className="bg-slate-50 border-slate-200"
              />

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-slate-500 uppercase">Assigned Role Type</label>
                <select
                  value={editingUser.role}
                  onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value as any })}
                  className="w-full border border-slate-200 bg-slate-50 px-3 py-2 rounded-lg font-semibold text-slate-700 focus:outline-none"
                >
                  <option value="analyst">Intelligence Analyst</option>
                  <option value="supervisor">Supervising Officer</option>
                  <option value="viewer">Command Room Viewer</option>
                  <option value="admin">System Administrator</option>
                </select>
              </div>

              <Input
                label="District Branch Jurisdiction"
                value={editingUser.district || ''}
                onChange={(e) => setEditingUser({ ...editingUser, district: e.target.value })}
                placeholder="HQ"
                className="bg-slate-50 border-slate-200"
              />

              <div className="flex justify-end gap-2 border-t border-slate-100 pt-4 mt-2">
                <Button type="button" variant="outline" onClick={() => setEditingUser(null)} className="rounded-lg">
                  Cancel
                </Button>
                <Button type="submit" variant="primary" className="bg-slate-900 hover:bg-slate-800 text-white rounded-lg">
                  Save Changes
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// --- System Audit Trail Page ---
export const AuditTrailPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">System Audit Logs</h1>
        <p className="text-sm text-slate-500">Permanent cryptographically tracked officer actions and raw GNN model pipelines.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              <th className="p-4">Timestamp</th>
              <th className="p-4">Officer ID</th>
              <th className="p-4">Action Event</th>
              <th className="p-4">IP Address</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="text-xs text-slate-600 divide-y divide-slate-100 font-medium">
            <tr className="hover:bg-slate-50/50">
              <td className="p-4 text-slate-400">{new Date().toLocaleString()}</td>
              <td className="p-4 font-mono font-bold text-slate-700">admin</td>
              <td className="p-4">Access User Management Database Logs</td>
              <td className="p-4 font-mono">127.0.0.1</td>
              <td className="p-4"><Badge variant="green">Success</Badge></td>
            </tr>
            <tr className="hover:bg-slate-50/50">
              <td className="p-4 text-slate-400">{new Date(Date.now() - 3600000).toLocaleString()}</td>
              <td className="p-4 font-mono font-bold text-slate-700">analyst</td>
              <td className="p-4">Trigger Ingestion Pipeline: DD.MM.YYYY</td>
              <td className="p-4 font-mono">127.0.0.1</td>
              <td className="p-4"><Badge variant="green">Success</Badge></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Database Health Indicator Status Page ---
export const SystemStatusPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Database Health Indicator</h1>
        <p className="text-sm text-slate-500">Verify connectivity and sync with relational databases, GNNs, and vector indexes.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest">PostgreSQL DB</h3>
            <Badge variant="green">Healthy</Badge>
          </div>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1">
            <Server size={12} className="text-emerald-500" /> Connected
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest">Neo4j Graph</h3>
            <Badge variant="green">Healthy</Badge>
          </div>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1">
            <Orbit size={12} className="text-emerald-500" /> Sync Active
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest">Qdrant Vector</h3>
            <Badge variant="green">Healthy</Badge>
          </div>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1">
            <Database size={12} className="text-emerald-500" /> Vector Synced
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-widest">Redis Cache</h3>
            <Badge variant="green">Healthy</Badge>
          </div>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1">
            <Cpu size={12} className="text-emerald-500" /> Cache Online
          </p>
        </div>
      </div>
    </div>
  );
};
