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
  login: (user: User, token: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  login: (user, token) => {
    localStorage.setItem('kpip_token', token);
    localStorage.setItem('kpip_user', JSON.stringify(user));
    set({ user, token });
  },
  logout: () => {
    localStorage.removeItem('kpip_token');
    localStorage.removeItem('kpip_user');
    set({ user: null, token: null });
  },
  isAuthenticated: () => {
    return !!get().token;
  },
}));

// Initialize store from localStorage if available
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('kpip_token');
  const userStr = localStorage.getItem('kpip_user');
  if (token && userStr) {
    try {
      const user = JSON.parse(userStr);
      useAuthStore.setState({ user, token });
    } catch (e) {
      localStorage.removeItem('kpip_token');
      localStorage.removeItem('kpip_user');
    }
  }
}
