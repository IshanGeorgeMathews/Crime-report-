import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import type { User } from '../stores/authStore';
import type { ApiResponse } from '../types/api';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const loginStore = useAuthStore((state) => state.login);
  const logoutStore = useAuthStore((state) => state.logout);

  const meQuery = useQuery<ApiResponse<User>, Error>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<User>>('/auth/me');
      return response.data;
    },
    enabled: useAuthStore((state) => state.isAuthenticated()),
  });

  const loginMutation = useMutation<
    ApiResponse<{ user: User; token: string }>,
    Error,
    { username: string; password?: string }
  >({
    mutationFn: async (credentials) => {
      const response = await api.post<ApiResponse<{ user: User; token: string }>>(
        '/auth/login',
        credentials
      );
      return response.data;
    },
    onSuccess: (response) => {
      if (response.success && response.data) {
        loginStore(response.data.user, response.data.token);
        queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      }
    },
  });

  const logoutMutation = useMutation<ApiResponse<void>, Error, void>({
    mutationFn: async () => {
      const response = await api.post<ApiResponse<void>>('/auth/logout');
      return response.data;
    },
    onSettled: () => {
      logoutStore();
      queryClient.clear();
    },
  });

  return {
    user: useAuthStore((state) => state.user),
    isAuthenticated: useAuthStore((state) => state.isAuthenticated()),
    isCheckingMe: meQuery.isFetching,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
  };
};
