# JungleLab Visuals

Aplicación web para crear y visualizar visuales inmersivos con p5.js, controles en tiempo real y mapeo MIDI. Incluye presets con estética de instalación audiovisual (neones, fog volumétrica, partículas, ruido procedural) y reactividad opcional al audio.

## Requisitos
- Node.js 18+
- Navegador con soporte WebMIDI y WebAudio (Chrome recomendado)

## Scripts
- `npm install` – instala dependencias.
- `npm run dev` – entorno de desarrollo Vite.
- `npm run build` – genera la build de producción.
- `npm run preview` – sirve la build generada.
- `npm run typecheck` – comprueba tipos de TypeScript.

## Funciones clave
- Render p5.js con capas de partículas, gradientes holográficos, niebla y deformaciones procedurales.
- Parámetros visuales editables en tiempo real por preset.
- Modo "Learn" para mapear CC de MIDI a cualquier parámetro con feedback visual.
- Reactividad al micrófono para modular intensidad, turbulencia y glow de los shaders simulados.
- Diseño UI oscuro con panel de control y canvas a pantalla completa.

## Desarrollo
1. `npm install`
2. `npm run dev`
3. Abre `http://localhost:5173` y habilita micrófono/MIDI cuando se solicite.
