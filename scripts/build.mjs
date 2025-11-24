import { build } from 'esbuild';
import { mkdir, readFile, writeFile } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const outDir = path.join(root, 'dist');

await mkdir(outDir, { recursive: true });

await build({
  entryPoints: [path.join(root, 'src', 'main.tsx')],
  bundle: true,
  outdir: outDir,
  format: 'esm',
  sourcemap: true,
  target: ['chrome120'],
  loader: { '.css': 'css' },
  jsx: 'automatic',
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production'),
  },
});

const indexPath = path.join(root, 'index.html');
const html = await readFile(indexPath, 'utf8');
const patched = html.replace('/src/main.tsx', './main.js');
await writeFile(path.join(outDir, 'index.html'), patched, 'utf8');

console.log('Build listo en', outDir);
