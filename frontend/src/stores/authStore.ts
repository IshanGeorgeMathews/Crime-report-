import { create } from 'zustand';

export interface User {
  id: string;
  username: string;
  fullName: string;
  role: 'admin' | 'supervisor' | 'analyst' | 'viewer';
  district?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isInitializing: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
  setInitializing: (v: boolean) => void;
  syncUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: {
    id: "admin-id",
    username: "admin",
    fullName: "System Administrator (Testing)",
    role: "admin",
    district: "PKD"
  },
  token: "mock-admin-token",
  isInitializing: false,
  login: (user, token) => {
    localStorage.setItem('kpip_token', token);
    localStorage.setItem('kpip_user', JSON.stringify(user));
    set({ user, token, isInitializing: false });
  },
  logout: () => {
    localStorage.removeItem('kpip_token');
    localStorage.removeItem('kpip_user');
    set({
      user: null,
      token: null,
      isInitializing: false
    });
  },
  isAuthenticated: () => {
    return get().token !== null && get().user !== null;
  },
  setInitializing: (v) => set({ isInitializing: v }),
  syncUser: (user) => {
    localStorage.setItem('kpip_user', JSON.stringify(user));
    set({ user });
  },
}));

// Load mock token on startup for testing
if (typeof window !== 'undefined') {
  useAuthStore.setState({
    user: {
      id: "admin-id",
      username: "admin",
      fullName: "System Administrator (Testing)",
      role: "admin",
      district: "PKD"
    },
    token: "mock-admin-token",
    isInitializing: false
  });
}
