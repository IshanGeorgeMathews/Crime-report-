import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useUiStore } from '../stores/uiStore';
import type { ApiResponse } from '../types/api';
import type { Job } from '../types/job';
import { useEffect } from 'react';

export const useQueue = (jobId?: string) => {
  const setActiveJobsCount = useUiStore((state) => state.setActiveJobsCount);

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

  // Sync active jobs count to uiStore for header status bar indicator
  const jobs = queueQuery.data?.data || [];
  const activeCount = jobs.filter((j) => j.status === 'running' || j.status === 'queued').length;
  
  useEffect(() => {
    setActiveJobsCount(activeCount);
  }, [activeCount, setActiveJobsCount]);

  return {
    job: jobQuery.data?.data,
    isFetchingJob: jobQuery.isFetching,
    jobError: jobQuery.error,
    
    queue: queueQuery.data?.data || [],
    isFetchingQueue: queueQuery.isFetching,
    queueError: queueQuery.error,
    refetchQueue: queueQuery.refetch,
  };
};
