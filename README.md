# AudioVisualizer

## Agregar nuevos presets

1. Crea una carpeta dentro de `src/presets/<nombre-del-preset>`.
2. Incluye un archivo `config.json` que siga el esquema definido en [`presets/schema.json`](presets/schema.json).
3. Crea un archivo `preset.ts` que exporte `config` y `createPreset`.
4. Opcionalmente añade `shader.wgsl` si el preset usa shaders personalizados.

La configuración se valida automáticamente al cargar la aplicación utilizando [Ajv](https://ajv.js.org/). Si el archivo `config.json` no cumple el esquema, el preset será omitido y se mostrará un error en la consola.
