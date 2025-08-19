import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',  // ← ESTO ES CRÍTICO
  server: {
    port: 3000,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      input: {
        main: './index.html',
      }
    }
  },
  assetsInclude: ['**/*.wgsl'],
  json: {
    stringify: false
  }
});