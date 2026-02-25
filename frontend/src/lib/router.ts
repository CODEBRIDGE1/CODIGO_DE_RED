/**
 * Simple Router for Svelte
 */
import { writable, derived } from 'svelte/store';

interface Route {
  path: string;
  component: any;
  meta?: {
    requiresAuth?: boolean;
    permission?: string;
  };
}

const currentPath = writable(window.location.pathname);

// Listen to popstate events (browser back/forward)
window.addEventListener('popstate', () => {
  currentPath.set(window.location.pathname);
});

export function navigate(path: string) {
  window.history.pushState({}, '', path);
  currentPath.set(path);
}

export function createRouter(routes: Route[]) {
  return derived(currentPath, $path => {
    const route = routes.find(r => r.path === $path) || routes.find(r => r.path === '*');
    return route;
  });
}

export { currentPath };
