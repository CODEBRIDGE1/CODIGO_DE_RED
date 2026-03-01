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
  photoUrl: string | null;
  permissions: string[];
  securityModules: string[];       // module keys from the user's security level
  securityLevelId: number | null;  // id del nivel de seguridad asignado
  securityLevelName: string | null;// nombre del nivel de seguridad
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

// Prevent concurrent refresh calls
let _refreshPromise: Promise<string | null> | null = null;

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false
  });

  const store = {
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
        const stored = JSON.parse(userJson);
        const user: User = {
          securityModules: [],
          securityLevelId: null,
          securityLevelName: null,
          photoUrl: null,
          ...stored
        };
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
    },

    /**
     * Intenta renovar el access token usando el refresh token.
     * Retorna el nuevo access token, o null si falla (sesión expirada).
     */
    refreshAccessToken: async (): Promise<string | null> => {
      if (_refreshPromise) return _refreshPromise;

      _refreshPromise = (async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return null;

        try {
          const base = (import.meta as any).env?.VITE_API_BASE_URL ?? '';
          const res = await fetch(`${base}/api/v1/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (!res.ok) {
            store.logout();
            return null;
          }

          const data = await res.json();
          const newAccess: string = data.access_token;
          const newRefresh: string = data.refresh_token;

          localStorage.setItem('access_token', newAccess);
          localStorage.setItem('refresh_token', newRefresh);
          update(s => ({ ...s, accessToken: newAccess, refreshToken: newRefresh }));
          return newAccess;
        } catch {
          store.logout();
          return null;
        } finally {
          _refreshPromise = null;
        }
      })();

      return _refreshPromise;
    },

    /**
     * fetch() wrapper que renueva el token automáticamente al recibir 401.
     * Úsalo en lugar de fetch() para todas las llamadas autenticadas.
     *
     * Usage: const res = await authStore.fetch('/api/v1/companies/', { method: 'GET' });
     */
    fetch: async (input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> => {
      const token = localStorage.getItem('access_token');
      const headers = new Headers(init.headers);
      if (token) headers.set('Authorization', `Bearer ${token}`);

      const res = await fetch(input, { ...init, headers });

      if (res.status === 401) {
        const newToken = await store.refreshAccessToken();
        if (!newToken) return res; // sesión expirada, el logout ya se hizo

        headers.set('Authorization', `Bearer ${newToken}`);
        return fetch(input, { ...init, headers });
      }

      return res;
    },
  };

  return store;
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
