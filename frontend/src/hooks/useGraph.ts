import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ApiResponse } from '../types/api';
import type { GraphData, GnnRecommendation } from '../types/graph';

export const useGraph = (personName?: string) => {
  const queryClient = useQueryClient();

  // Query node-edge network data
  const networkQuery = useQuery<ApiResponse<GraphData>, Error>({
    queryKey: ['graph', 'network', personName],
    queryFn: async () => {
      const response = await api.get<ApiResponse<GraphData>>('/graph/query', {
        params: personName ? { person: personName } : {},
      });
      return response.data;
    },
  });

  // Query graph database statistics
  const statsQuery = useQuery<ApiResponse<any>, Error>({
    queryKey: ['graph', 'stats'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<any>>('/graph/stats');
      return response.data;
    },
  });

  // Query GNN hidden associate suggestions
  const associatesQuery = useQuery<ApiResponse<GnnRecommendation[]>, Error>({
    queryKey: ['graph', 'associates', personName],
    queryFn: async () => {
      const response = await api.get<ApiResponse<GnnRecommendation[]>>(`/graph/associates/${personName}`);
      return response.data;
    },
    enabled: !!personName,
  });

  // Clean graph nodes database mutation
  const cleanGraphMutation = useMutation<ApiResponse<{ removedCount: number }>, Error, void>({
    mutationFn: async () => {
      const response = await api.post<ApiResponse<{ removedCount: number }>>('/graph/clean');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['graph'] });
    },
  });

  return {
    graphData: networkQuery.data?.data || { nodes: [], edges: [] },
    isFetchingGraph: networkQuery.isFetching,
    graphError: networkQuery.error,

    stats: statsQuery.data?.data,
    isFetchingStats: statsQuery.isFetching,

    associates: associatesQuery.data?.data || [],
    isFetchingAssociates: associatesQuery.isFetching,

    cleanGraph: cleanGraphMutation.mutateAsync,
    isCleaning: cleanGraphMutation.isPending,
  };
};
