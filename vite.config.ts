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
      // Externalizar los módulos de Tauri para que no falle el build
      external: ['@tauri-apps/api/event', '@tauri-apps/api/window'],
      output: {
        // Configurar cómo manejar los módulos externos
        globals: {
          '@tauri-apps/api/event': 'TauriEvent',
          '@tauri-apps/api/window': 'TauriWindow'
        }
      }
    }
  },
  assetsInclude: ['**/*.wgsl'],
  json: {
    stringify: false
  },
  // Configurar el manejo de dependencias opcionales
  optimizeDeps: {
    exclude: ['@tauri-apps/api']
  }
});