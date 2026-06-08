import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './stores/authStore';
import { useAuth } from './hooks/useAuth';
import { AuthenticatedLayout } from './components/layout/AuthenticatedLayout';
import {
  LoginPage,
  DashboardPage,
  ConsolidatePage,
  QueuePage,
  ReviewQueuePage,
  ReportListPage,
  ReportDetailPage,
  ProfileListPage,
  ProfileDetailPage,
  GraphExplorerPage,
  SearchPage,
  SchedulePage,
  UserManagementPage,
  AuditTrailPage,
  SystemStatusPage,
} from './features/stubs';

// Initialize React Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // Intranet environment optimization
      retry: 1,
    },
  },
});

// Guard: Protected Routes (must be authenticated + validated)
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

// Guard: Role-based Authorization Routes
const RoleRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles: ('admin' | 'supervisor' | 'analyst' | 'viewer')[];
}> = ({ children, allowedRoles }) => {
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Endpoint */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Intranet Shell */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AuthenticatedLayout />
              </ProtectedRoute>
            }
          >
            {/* Direct lander */}
            <Route index element={<Navigate to="/dashboard" replace />} />
            
            <Route path="dashboard" element={<DashboardPage />} />
            
            {/* Analyst & Above operations */}
            <Route
              path="consolidate"
              element={
                <RoleRoute allowedRoles={['admin', 'supervisor', 'analyst']}>
                  <ConsolidatePage />
                </RoleRoute>
              }
            />
            <Route
              path="queue"
              element={
                <RoleRoute allowedRoles={['admin', 'supervisor', 'analyst']}>
                  <QueuePage />
                </RoleRoute>
              }
            />

            {/* Supervisor & Above operations */}
            <Route
              path="review"
              element={
                <RoleRoute allowedRoles={['admin', 'supervisor']}>
                  <ReviewQueuePage />
                </RoleRoute>
              }
            />
            
            {/* All role operations */}
            <Route path="reports" element={<ReportListPage />} />
            <Route path="reports/:id" element={<ReportDetailPage />} />
            <Route path="profiles" element={<ProfileListPage />} />
            <Route path="profiles/:id" element={<ProfileDetailPage />} />
            <Route path="graph" element={<GraphExplorerPage />} />
            <Route path="search" element={<SearchPage />} />

            {/* Schedules and Administrative routes */}
            <Route
              path="schedules"
              element={
                <RoleRoute allowedRoles={['admin', 'supervisor']}>
                  <SchedulePage />
                </RoleRoute>
              }
            />
            <Route
              path="admin/users"
              element={
                <RoleRoute allowedRoles={['admin']}>
                  <UserManagementPage />
                </RoleRoute>
              }
            />
            <Route
              path="admin/audit"
              element={
                <RoleRoute allowedRoles={['admin']}>
                  <AuditTrailPage />
                </RoleRoute>
              }
            />
            <Route
              path="admin/system"
              element={
                <RoleRoute allowedRoles={['admin']}>
                  <SystemStatusPage />
                </RoleRoute>
              }
            />
            
            {/* Catchall redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
export default App;
