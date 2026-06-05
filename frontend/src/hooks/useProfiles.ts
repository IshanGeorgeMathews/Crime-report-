import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ApiResponse, PaginatedResponse } from '../types/api';
import type { PersonProfile, ProfileCase, ProfileRelation, ProfileActivity } from '../types/profile';

export const useProfiles = (profileId?: string) => {
  const queryClient = useQueryClient();

  // Query paginated and filterable profiles list
  const listQuery = useQuery<ApiResponse<PaginatedResponse<PersonProfile>>, Error>({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<PaginatedResponse<PersonProfile>>>('/profiles');
      return response.data;
    },
  });

  // Query individual suspect profile details (including cases, relations, activities)
  const detailQuery = useQuery<
    ApiResponse<PersonProfile & { cases: ProfileCase[]; relations: ProfileRelation[]; activities: ProfileActivity[] }>,
    Error
  >({
    queryKey: ['profile', profileId],
    queryFn: async () => {
      const response = await api.get<
        ApiResponse<PersonProfile & { cases: ProfileCase[]; relations: ProfileRelation[]; activities: ProfileActivity[] }>
      >(`/profiles/${profileId}`);
      return response.data;
    },
    enabled: !!profileId,
  });

  // Update suspect profile mutation
  const updateMutation = useMutation<ApiResponse<PersonProfile>, Error, Partial<PersonProfile>>({
    mutationFn: async (profileUpdates) => {
      const response = await api.put<ApiResponse<PersonProfile>>(
        `/profiles/${profileId}`,
        profileUpdates
      );
      return response.data;
    },
    onSuccess: (response) => {
      if (response.success) {
        queryClient.invalidateQueries({ queryKey: ['profile', profileId] });
        queryClient.invalidateQueries({ queryKey: ['profiles'] });
      }
    },
  });

  // Query review queue (VEG candidate names)
  const reviewQueueQuery = useQuery<ApiResponse<any[]>, Error>({
    queryKey: ['reviewQueue'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<any[]>>('/review');
      return response.data;
    },
  });

  // Review candidate approval/rejection mutations
  const reviewActionMutation = useMutation<
    ApiResponse<{ id: string; status: string }>,
    Error,
    { id: string; action: 'approve' | 'reject' }
  >({
    mutationFn: async ({ id, action }) => {
      const response = await api.post<ApiResponse<{ id: string; status: string }>>(
        `/review/${id}/${action}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] });
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });

  return {
    profiles: listQuery.data?.data?.items || [],
    totalProfiles: listQuery.data?.data?.total || 0,
    isFetchingProfiles: listQuery.isFetching,
    profilesError: listQuery.error,

    profileDetail: detailQuery.data?.data,
    isFetchingDetail: detailQuery.isFetching,
    detailError: detailQuery.error,

    updateProfile: updateMutation.mutateAsync,
    isUpdatingProfile: updateMutation.isPending,

    reviewQueue: reviewQueueQuery.data?.data || [],
    isFetchingReviewQueue: reviewQueueQuery.isFetching,
    reviewQueueError: reviewQueueQuery.error,
    executeReviewAction: reviewActionMutation.mutateAsync,
    isExecutingReview: reviewActionMutation.isPending,
  };
};
