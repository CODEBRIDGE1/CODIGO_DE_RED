/**
 * Auth Store - Estado global de autenticación
 */
import { writable, derived } from 'svelte/store';

export interface User {
  id: string;
  email: string;
  fullName: string;
  tenantId: number | null;
  isSuperadmin: boolean;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false
  });

  return {
    subscribe,
    
    login: (accessToken: string, refreshToken: string, user: User) => {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
      
      set({
        user,
        accessToken,
        refreshToken,
        isAuthenticated: true
      });
    },
    
    logout: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false
      });
    },
    
    loadFromStorage: () => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const userJson = localStorage.getItem('user');
      
      if (accessToken && refreshToken && userJson) {
        const user = JSON.parse(userJson);
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true
        });
        return true;
      }
      return false;
    },
    
    updateUser: (user: User) => {
      localStorage.setItem('user', JSON.stringify(user));
      update(state => ({ ...state, user }));
    }
  };
}

export const authStore = createAuthStore();

// Derived store para verificar permisos
export const hasPermission = derived(
  authStore,
  $auth => (permission: string) => {
    if (!$auth.user) return false;
    if ($auth.user.isSuperadmin) return true;
    return $auth.user.permissions.includes(permission);
  }
);
