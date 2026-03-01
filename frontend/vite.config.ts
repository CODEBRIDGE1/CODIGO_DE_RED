import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  // VITE_PROXY_TARGET: internal Docker target (http://api:8000 in production)
  // VITE_API_BASE_URL: browser-side prefix (empty in production = relative URLs)
  const apiTarget = process.env.VITE_PROXY_TARGET || env.VITE_PROXY_TARGET ||
                    process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL ||
                    'http://localhost:8001';

  return {
    plugins: [svelte()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      hmr: {
        overlay: false,
        clientPort: 5173
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          autoRewrite: true,
          protocolRewrite: 'http'
        }
      }
    },
    logLevel: 'warn'
  };
});
