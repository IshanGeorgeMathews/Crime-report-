import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/api';
import type { ApiResponse } from '../types/api';

export const useConsolidate = () => {
  const queryClient = useQueryClient();

  const uploadMutation = useMutation<
    ApiResponse<{ jobId: string }>,
    Error,
    { date: string; files: File[] }
  >({
    mutationFn: async ({ date, files }) => {
      const formData = new FormData();
      formData.append('date', date);
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await api.post<ApiResponse<{ jobId: string }>>(
        '/consolidate/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate active queues to show new running consolidation job
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  return {
    uploadFiles: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
  };
};
