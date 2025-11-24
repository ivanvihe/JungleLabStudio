import { build } from 'esbuild';
import path from 'path';
import { fileURLToPath } from 'url';
import './build.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');

const context = await build({
  entryPoints: [path.join(root, 'src', 'main.tsx')],
  bundle: true,
  outdir: path.join(root, 'dist'),
  format: 'esm',
  sourcemap: true,
  target: ['chrome120'],
  loader: { '.css': 'css' },
  jsx: 'automatic',
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
  watch: {
    onRebuild(error) {
      if (error) {
        console.error('Error reconstruyendo', error);
      } else {
        console.log('Renderer reconstruido');
      }
    },
  },
});

console.log('Watch activo para renderer');
await context;
