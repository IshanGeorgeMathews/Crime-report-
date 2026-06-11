import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useUiStore } from '../stores/uiStore';
import type { ApiResponse } from '../types/api';
import type { Job } from '../types/job';
import { useEffect } from 'react';

export const useQueue = (jobId?: string) => {
  const queryClient = useQueryClient();

  // Query single job details
  const jobQuery = useQuery<ApiResponse<Job>, Error>({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const response = await api.get<ApiResponse<Job>>(`/jobs/${jobId}`);
      return response.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data?.data;
      return job && (job.status === 'running' || job.status === 'queued') ? 3000 : false;
    },
  });

  // Query all active and recent jobs
  const queueQuery = useQuery<ApiResponse<Job[]>, Error>({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<Job[]>>('/jobs');
      return response.data;
    },
    refetchInterval: (query) => {
      const jobs = query.state.data?.data || [];
      const hasActive = jobs.some((j) => j.status === 'running' || j.status === 'queued');
      return hasActive ? 3000 : 15000; // Poll faster if there are running tasks
    },
  });

  // Cancel a job and undo changes
  const cancelMutation = useMutation<ApiResponse<void>, Error, string>({
    mutationFn: async (id: string) => {
      const response = await api.post<ApiResponse<void>>(`/jobs/${id}/cancel`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  // Stop a job (pause it, keep intermediate state)
  const stopMutation = useMutation<ApiResponse<void>, Error, string>({
    mutationFn: async (id: string) => {
      const response = await api.post<ApiResponse<void>>(`/jobs/${id}/stop`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  // Resume/Run back a stopped/failed job
  const resumeMutation = useMutation<ApiResponse<void>, Error, string>({
    mutationFn: async (id: string) => {
      const response = await api.post<ApiResponse<void>>(`/jobs/${id}/resume`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  // Delete a job from the queue database
  const deleteMutation = useMutation<ApiResponse<void>, Error, string>({
    mutationFn: async (id: string) => {
      const response = await api.delete<ApiResponse<void>>(`/jobs/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  // Sync active jobs count to uiStore for header status bar indicator
  const jobs = queueQuery.data?.data || [];
  const activeCount = jobs.filter((j) => j.status === 'running' || j.status === 'queued').length;
  
  useEffect(() => {
    useUiStore.getState().setActiveJobsCount(activeCount);
  }, [activeCount]);

  return {
    job: jobQuery.data?.data,
    isFetchingJob: jobQuery.isFetching,
    jobError: jobQuery.error,
    
    queue: queueQuery.data?.data || [],
    isFetchingQueue: queueQuery.isFetching,
    queueError: queueQuery.error,
    refetchQueue: queueQuery.refetch,

    cancelJob: cancelMutation.mutateAsync,
    isCancelling: cancelMutation.isPending,
    cancelError: cancelMutation.error,

    stopJob: stopMutation.mutateAsync,
    isStopping: stopMutation.isPending,
    stopError: stopMutation.error,

    resumeJob: resumeMutation.mutateAsync,
    isResuming: resumeMutation.isPending,
    resumeError: resumeMutation.error,

    deleteJob: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    deleteError: deleteMutation.error,
  };
};

