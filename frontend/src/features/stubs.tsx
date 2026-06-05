import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useReports } from '../hooks/useReports';
import { useProfiles } from '../hooks/useProfiles';
import { useGraph } from '../hooks/useGraph';
import { useQueue } from '../hooks/useQueue';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { Users, Folder, Orbit } from 'lucide-react';

// --- Login Page ---
export const LoginPage: React.FC = () => {
  const { login, isLoggingIn } = useAuth();
  const [username, setUsername] = useState('analyst');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await login({ username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-police-dark text-white p-6">
      <div className="max-w-md w-full panel-glass bg-slate-900/60 p-8 rounded-xl border border-police-slate shadow-premium text-center space-y-6">
        <div className="flex flex-col items-center gap-2">
          <div className="w-16 h-16 rounded-full bg-police-light flex items-center justify-center text-police-dark font-extrabold text-2xl shadow-premium">
            KP
          </div>
          <h2 className="text-xl font-bold text-white tracking-wider">KERALA POLICE</h2>
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-widest">// SECRET // INTELLIGENCE PLATFORM</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 text-left">
          <Input
            label="Officer Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="bg-slate-800 border-slate-700 text-white placeholder-slate-500 focus:border-police-light"
          />
          <Input
            label="Access Pin / Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="bg-slate-800 border-slate-700 text-white placeholder-slate-500 focus:border-police-light"
          />
          <div className="pt-2">
            <Button type="submit" className="w-full text-police-dark bg-police-light hover:bg-teal-400 font-bold" isLoading={isLoggingIn}>
              Establish Secure Session
            </Button>
          </div>
        </form>

        <div className="text-[10px] text-slate-500 font-medium">
          Authorized personnel only. Sessions are audited in real-time under Kerala Police IT Act.
        </div>
      </div>
    </div>
  );
};

// --- Dashboard Page ---
export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-police-dark">Command Center Dashboard</h1>
          <p className="text-sm text-slate-500">Welcome, officer {user?.fullName}. Role: {user?.role.toUpperCase()}</p>
        </div>
        <Badge variant="green">Online</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-5 rounded-xl shadow-premium border border-slate-100 flex items-center gap-4">
          <div className="w-12 h-12 bg-sky-100 text-sky-700 rounded-lg flex items-center justify-center shrink-0">
            <Folder size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-500">Consolidated Reports</h3>
            <p className="text-2xl font-black text-police-dark">24</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-premium border border-slate-100 flex items-center gap-4">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-lg flex items-center justify-center shrink-0">
            <Users size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-500">Suspect PP Dossiers</h3>
            <p className="text-2xl font-black text-police-dark">1,432</p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-premium border border-slate-100 flex items-center gap-4">
          <div className="w-12 h-12 bg-amber-100 text-amber-700 rounded-lg flex items-center justify-center shrink-0">
            <Orbit size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-500">Graph Database Nodes</h3>
            <p className="text-2xl font-black text-police-dark">142</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white p-6 rounded-xl shadow-premium border border-slate-100 space-y-4">
        <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" className="bg-police-slate hover:bg-police-hover text-white">Upload New Files</Button>
          <Button variant="outline">Search Suspects</Button>
          <Button variant="outline">Open Graph View</Button>
        </div>
      </div>
    </div>
  );
};

// --- Consolidate Page ---
export const ConsolidatePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Consolidate Daily Reports</h1>
        <p className="text-sm text-slate-500">Upload district docx reports to translate, classify and consolidate.</p>
      </div>
      <div className="bg-white p-8 rounded-xl shadow-premium border border-slate-100 text-center space-y-4">
        <div className="border-2 border-dashed border-slate-300 rounded-lg p-12 hover:border-police-blue cursor-pointer transition-colors">
          <p className="text-sm font-semibold text-slate-600">Drag & drop district .docx files here</p>
          <p className="text-xs text-slate-400 mt-1">Accepts multiple reports up to 10MB per file</p>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="outline">Cancel</Button>
          <Button variant="primary">Begin Processing Pipeline</Button>
        </div>
      </div>
    </div>
  );
};

// --- Queue Page ---
export const QueuePage: React.FC = () => {
  const { queue } = useQueue();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Celery Processing Queue</h1>
        <p className="text-sm text-slate-500">Monitor running tasks, GNN trainings andScheduled runs.</p>
      </div>
      <div className="bg-white rounded-xl shadow-premium border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100 text-xs font-bold text-slate-500 uppercase">
              <th className="p-4">Task Type</th>
              <th className="p-4">Status</th>
              <th className="p-4">Progress</th>
              <th className="p-4">Current Step</th>
              <th className="p-4">Triggered By</th>
            </tr>
          </thead>
          <tbody className="text-sm text-slate-600 divide-y divide-slate-100">
            {queue.map((job) => (
              <tr key={job.id}>
                <td className="p-4 font-semibold text-police-dark">{job.jobType.toUpperCase()}</td>
                <td className="p-4"><Badge variant={job.status === 'running' ? 'blue' : 'gray'}>{job.status}</Badge></td>
                <td className="p-4">{job.progress}%</td>
                <td className="p-4">{job.currentStep || 'Waiting...'}</td>
                <td className="p-4">{job.createdBy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Review Queue (VEG) Page ---
export const ReviewQueuePage: React.FC = () => {
  const { reviewQueue } = useProfiles();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Review Queue (VEG)</h1>
        <p className="text-sm text-slate-500">Approve or reject candidate names extracted by the NER pipeline.</p>
      </div>
      <div className="bg-white rounded-xl shadow-premium border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100 text-xs font-bold text-slate-500 uppercase">
              <th className="p-4">Extracted Candidate</th>
              <th className="p-4">Source Mention</th>
              <th className="p-4">NER Score</th>
              <th className="p-4">Action Flags</th>
              <th className="p-4 text-right">Decisions</th>
            </tr>
          </thead>
          <tbody className="text-sm text-slate-600 divide-y divide-slate-100">
            {reviewQueue.map((item) => (
              <tr key={item.id}>
                <td className="p-4 font-semibold text-police-dark">{item.name}</td>
                <td className="p-4 text-xs italic">{item.source}</td>
                <td className="p-4">{item.extractionMethod}</td>
                <td className="p-4 text-xs text-rose-600 font-semibold">{item.anomalyFlags}</td>
                <td className="p-4 text-right space-x-2">
                  <Button variant="outline" className="px-2.5 py-1 text-xs text-rose-600 border-rose-200 hover:bg-rose-50">Reject</Button>
                  <Button variant="primary" className="px-2.5 py-1 text-xs bg-emerald-600 hover:bg-emerald-700">Approve</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Reports Page ---
export const ReportListPage: React.FC = () => {
  const { reports } = useReports();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Consolidated Report Library</h1>
        <p className="text-sm text-slate-500">Access historical daily consolidated documents.</p>
      </div>
      <div className="bg-white rounded-xl shadow-premium border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100 text-xs font-bold text-slate-500 uppercase">
              <th className="p-4">Report Date</th>
              <th className="p-4">Reference File #</th>
              <th className="p-4">Events</th>
              <th className="p-4">Forecasts</th>
              <th className="p-4">Social Media</th>
              <th className="p-4 text-right">Downloads</th>
            </tr>
          </thead>
          <tbody className="text-sm text-slate-600 divide-y divide-slate-100">
            {reports.map((rep) => (
              <tr key={rep.id}>
                <td className="p-4 font-bold text-police-dark">{rep.reportDate}</td>
                <td className="p-4">{rep.refNumber}</td>
                <td className="p-4"><Badge variant="blue">{rep.eventCount}</Badge></td>
                <td className="p-4"><Badge variant="amber">{rep.forecastCount}</Badge></td>
                <td className="p-4"><Badge variant="green">{rep.socialMediaCount}</Badge></td>
                <td className="p-4 text-right">
                  <Button variant="outline" className="text-xs">Download Word Doc</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const ReportDetailPage: React.FC = () => <div>Report Detail</div>;

// --- Profiles Page ---
export const ProfileListPage: React.FC = () => {
  const { profiles } = useProfiles();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Suspect dossiers (PP Profiles)</h1>
        <p className="text-sm text-slate-500">Manage individuals under watch and export regulatory dossiers.</p>
      </div>
      <div className="bg-white rounded-xl shadow-premium border border-slate-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-100 text-xs font-bold text-slate-500 uppercase">
              <th className="p-4">PP ID</th>
              <th className="p-4">Suspect Name</th>
              <th className="p-4">Parentage</th>
              <th className="p-4">Police Station</th>
              <th className="p-4">Classification</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody className="text-sm text-slate-600 divide-y divide-slate-100">
            {profiles.map((prof) => (
              <tr key={prof.id}>
                <td className="p-4 font-mono font-semibold text-slate-500">{prof.ppId}</td>
                <td className="p-4 font-bold text-police-dark">{prof.name}</td>
                <td className="p-4">{prof.parentage}</td>
                <td className="p-4">{prof.policeStation}</td>
                <td className="p-4"><Badge variant="red">{prof.activityType}</Badge></td>
                <td className="p-4"><Badge variant="green">{prof.reviewStatus}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const ProfileDetailPage: React.FC = () => <div>Profile Detail</div>;

// --- Graph Explorer Page ---
export const GraphExplorerPage: React.FC = () => {
  const { stats } = useGraph();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Intelligence Network Explorer</h1>
        <p className="text-sm text-slate-500">Interactively traverse associations in the Neo4j Graph DB.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-5 rounded-xl shadow-premium border border-slate-100 md:col-span-1 space-y-4">
          <h3 className="text-sm font-bold text-slate-700 uppercase">Graph Data</h3>
          {stats && (
            <div className="space-y-2 text-xs text-slate-600 font-semibold">
              <div className="flex justify-between"><span>Nodes Total:</span><span>{stats.total_nodes}</span></div>
              <div className="flex justify-between"><span>Edges Total:</span><span>{stats.total_edges}</span></div>
              <div className="flex justify-between"><span>Individuals:</span><span>{stats.individual_nodes}</span></div>
              <div className="flex justify-between"><span>Crimes:</span><span>{stats.crime_nodes}</span></div>
            </div>
          )}
        </div>
        <div className="bg-slate-900 rounded-xl min-h-[400px] md:col-span-3 flex items-center justify-center border border-slate-800 text-slate-400 font-semibold shadow-premium">
          vis.js canvas loader (depth = 1)...
        </div>
      </div>
    </div>
  );
};

// --- Search Page ---
export const SearchPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-police-dark">Unified Search</h1>
        <p className="text-sm text-slate-500">Perform SQL relational filters and Qdrant semantic vector similarity checks.</p>
      </div>
      <div className="bg-white p-6 rounded-xl shadow-premium border border-slate-100 space-y-4">
        <Input placeholder="Enter natural language query: e.g. Maoist cadre arrest Kozhikode..." />
        <div className="flex gap-2">
          <Button variant="primary">Qdrant Semantic Search</Button>
          <Button variant="outline">Relational SQL Search</Button>
        </div>
      </div>
    </div>
  );
};

// --- Schedules Page ---
export const SchedulePage: React.FC = () => (
  <div className="space-y-6">
    <h1 className="text-2xl font-bold text-police-dark">Ingestion Schedules</h1>
    <p className="text-sm text-slate-500">Configure file watch cron jobs and automation triggers.</p>
  </div>
);

// --- User Management Page ---
export const UserManagementPage: React.FC = () => (
  <div className="space-y-6">
    <h1 className="text-2xl font-bold text-police-dark">Officer Directory</h1>
    <p className="text-sm text-slate-500">Manage analyst and supervisor platform access permissions.</p>
  </div>
);

// --- Audit Trail Page ---
export const AuditTrailPage: React.FC = () => (
  <div className="space-y-6">
    <h1 className="text-2xl font-bold text-police-dark">System Audit Logs</h1>
    <p className="text-sm text-slate-500">Permanent cryptographically tracked user actions.</p>
  </div>
);

// --- System Status Page ---
export const SystemStatusPage: React.FC = () => (
  <div className="space-y-6">
    <h1 className="text-2xl font-bold text-police-dark">Database Health Indicator</h1>
    <p className="text-sm text-slate-500">Verify Neo4j, Redis, Qdrant and Ollama connectivity.</p>
  </div>
);
