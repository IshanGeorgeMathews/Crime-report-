import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ApiResponse } from '../types/api';

export interface UserListItem {
  id: string;
  username: string;
  fullName: string;
  role: 'admin' | 'supervisor' | 'analyst' | 'viewer';
  district?: string;
  is_active: boolean;
  last_login_at?: string;
  created_at: string;
}

export const useUsers = () => {
  const queryClient = useQueryClient();

  // Query all users (admin only)
  const usersQuery = useQuery<ApiResponse<UserListItem[]>, Error>({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get<ApiResponse<UserListItem[]>>('/admin/users');
      return response.data;
    },
  });

  // Create a new user (admin only)
  const createUserMutation = useMutation<
    ApiResponse<UserListItem>,
    Error,
    Omit<UserListItem, 'id' | 'is_active' | 'created_at'> & { password: string }
  >({
    mutationFn: async (newUser) => {
      const response = await api.post<ApiResponse<UserListItem>>('/admin/users', newUser);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Update user role, district, full name, or active status (admin only)
  const updateUserMutation = useMutation<
    ApiResponse<UserListItem>,
    Error,
    { id: string; fullName?: string; role?: string; district?: string; isActive?: boolean }
  >({
    mutationFn: async ({ id, ...updates }) => {
      const response = await api.put<ApiResponse<UserListItem>>(`/admin/users/${id}`, updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Deactivate a user (admin only)
  const deactivateUserMutation = useMutation<ApiResponse<any>, Error, string>({
    mutationFn: async (id) => {
      const response = await api.delete<ApiResponse<any>>(`/admin/users/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Change password for any authenticated user
  const changePasswordMutation = useMutation<
    ApiResponse<any>,
    Error,
    { old_password: string; new_password: string }
  >({
    mutationFn: async (payload) => {
      const response = await api.post<ApiResponse<any>>('/auth/change-password', payload);
      return response.data;
    },
  });

  return {
    users: usersQuery.data?.data || [],
    isFetchingUsers: usersQuery.isFetching,
    usersError: usersQuery.error,
    refetchUsers: usersQuery.refetch,

    createUser: createUserMutation.mutateAsync,
    isCreatingUser: createUserMutation.isPending,
    createUserError: createUserMutation.error,

    updateUser: updateUserMutation.mutateAsync,
    isUpdatingUser: updateUserMutation.isPending,
    updateUserError: updateUserMutation.error,

    deactivateUser: deactivateUserMutation.mutateAsync,
    isDeactivatingUser: deactivateUserMutation.isPending,
    deactivateUserError: deactivateUserMutation.error,

    changePassword: changePasswordMutation.mutateAsync,
    isChangingPassword: changePasswordMutation.isPending,
    changePasswordError: changePasswordMutation.error,
  };
};
