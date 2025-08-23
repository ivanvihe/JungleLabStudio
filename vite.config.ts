import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    port: 3000,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      input: {
        main: './index.html',
      },
      // Externalizar las APIs de Tauri para evitar errores de build en Electron
      external: [
        '@tauri-apps/api/event',
        '@tauri-apps/api/window',
        '@tauri-apps/api/fs',
        '@tauri-apps/api/path',
        '@tauri-apps/api/dialog',
        '@tauri-apps/api/shell',
        '@tauri-apps/api/app',
        '@tauri-apps/api/os',
        '@tauri-apps/api',
        // Magenta relies on heavy Node-specific modules; exclude it from Vite bundling
        '@magenta/music'
      ]
    }
  },
  assetsInclude: ['**/*.wgsl'],
  json: {
    stringify: false
  },
  css: {
    modules: {
      localsConvention: 'camelCase'
    }
  },
  // Configurar el manejo de dependencias opcionales
  optimizeDeps: {
    exclude: [
      '@tauri-apps/api',
      '@tauri-apps/api/event',
      '@tauri-apps/api/window',
      '@tauri-apps/api/fs',
      '@tauri-apps/api/path',
      '@tauri-apps/api/dialog',
      '@tauri-apps/api/shell',
      '@tauri-apps/api/app',
      '@tauri-apps/api/os',
      // Avoid pre-bundling the Magenta music library
      '@magenta/music'
    ]
  }
});
