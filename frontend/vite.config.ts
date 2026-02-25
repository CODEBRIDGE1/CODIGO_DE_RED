import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiUrl = env.VITE_API_BASE_URL || 'http://localhost:8001';
  
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
          target: apiUrl,
          changeOrigin: true,
          secure: false,
          rewrite: undefined
        }
      }
    },
    define: {
      '__API_URL__': JSON.stringify(apiUrl)
    },
    logLevel: 'warn'
  };
});
