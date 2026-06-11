import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { api } from '../lib/api';
import { useAuthStore } from '../stores/authStore';
import type { User } from '../stores/authStore';
import type { ApiResponse } from '../types/api';

export const useAuth = () => {
  const queryClient = useQueryClient();
  const loginStore = useAuthStore((state) => state.login);
  const logoutStore = useAuthStore((state) => state.logout);
  const syncUser = useAuthStore((state) => state.syncUser);
  const setInitializing = useAuthStore((state) => state.setInitializing);
  const token = useAuthStore((state) => state.token);
  const isInitializing = useAuthStore((state) => state.isInitializing);

  // Validate stored token on startup by calling /auth/me
  const meQuery = useQuery<ApiResponse<User>, Error>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<User>>('/auth/me');
      return response.data;
    },
    enabled: !!token, // Only run when there's a stored token
    retry: false, // Don't retry — if token is bad, log out
  });

  // Sync /auth/me result to the store
  useEffect(() => {
    if (meQuery.isSuccess && meQuery.data?.data) {
      // Token is valid — sync user data from the server
      syncUser(meQuery.data.data);
      setInitializing(false);
    } else if (meQuery.isError) {
      // Token is invalid/expired — clear everything and force re-login
      logoutStore();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meQuery.isSuccess, meQuery.isError, meQuery.data]);

  // If there's no token at all, initialization is already done (handled in authStore)

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
    isInitializing,
    isCheckingMe: meQuery.isFetching,
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    logout: logoutMutation.mutateAsync,
    isLoggingOut: logoutMutation.isPending,
  };
};
