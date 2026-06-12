import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ApiResponse } from '../types/api';
import type { GraphData, GnnRecommendation } from '../types/graph';

export type GraphQueryType = 'all' | 'node' | 'date' | 'crime';

export interface GraphQueryParams {
  queryType: GraphQueryType;
  centerNodeId?: string;
  date?: string;       // DD.MM.YYYY
  crimeKeyword?: string;
  depth?: number;
  startDate?: string;
  endDate?: string;
  minWeight?: number;
}

export const useGraph = () => {
  const queryClient = useQueryClient();

  // On-demand graph query mutation
  const graphMutation = useMutation<ApiResponse<GraphData>, Error, GraphQueryParams>({
    mutationFn: async (params) => {
      const searchParams: Record<string, string> = {
        queryType: params.queryType,
        depth: String(params.depth ?? 1),
      };
      if (params.centerNodeId) searchParams.centerNodeId = params.centerNodeId;
      if (params.date) searchParams.date = params.date;
      if (params.crimeKeyword) searchParams.crimeKeyword = params.crimeKeyword;
      if (params.startDate) searchParams.startDate = params.startDate;
      if (params.endDate) searchParams.endDate = params.endDate;
      if (params.minWeight !== undefined) searchParams.minWeight = String(params.minWeight);

      const response = await api.get<ApiResponse<GraphData>>('/graph/query', {
        params: searchParams,
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

  const fetchAssociates = async (personName: string) => {
    const response = await api.get<ApiResponse<GnnRecommendation[]>>(
      `/graph/associates/${encodeURIComponent(personName)}`
    );
    return response.data.data || [];
  };

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
    graphData: graphMutation.data?.data || { nodes: [], edges: [] },
    isFetchingGraph: graphMutation.isPending,
    graphError: graphMutation.error,
    queryGraph: graphMutation.mutateAsync,

    stats: statsQuery.data?.data,
    isFetchingStats: statsQuery.isFetching,

    fetchAssociates,
    associates: [] as GnnRecommendation[],
    isFetchingAssociates: false,

    cleanGraph: cleanGraphMutation.mutateAsync,
    isCleaning: cleanGraphMutation.isPending,
  };
};
