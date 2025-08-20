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
      // Externalizar el módulo de Tauri para que no falle el build
      external: ['@tauri-apps/api/event'],
      output: {
        // Configurar cómo manejar los módulos externos
        globals: {
          '@tauri-apps/api/event': 'TauriEvent'
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