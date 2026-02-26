import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiTarget = process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL || 'http://localhost:8001';

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
