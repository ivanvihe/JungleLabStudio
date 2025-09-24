# UI Redesign Audit: Steps 1-2

## 1. Auditoría de la UI actual

### Arquitectura general
- `src/App.tsx` orquesta la aplicación completa y ahora monta un layout inspirado en Proxmox compuesto por `ProxmoxShell`, `ProxmoxSidebar`, `ProxmoxMainArea`, `TaskActivityPanel` y `FooterPanel`, integrando barra superior, árbol lateral, escenario central y paneles colapsables.【F:src/App.tsx†L1261-L1609】
- Los estilos de layout se concentran en `src/components/layout/ProxmoxLayout.css`, donde se define una cuadrícula de tres columnas con sidebar fija, área central expansible y panel derecho/inferior colapsable, además de los breakpoints responsivos.【F:src/components/layout/ProxmoxLayout.css†L1-L212】

### Componentes principales
- **TopBar** (`src/components/TopBar.tsx`): barra superior con secciones para estado MIDI, BPM, audio y controles rápidos (recursos, limpiar, ocultar UI, fullscreen, settings, Launchpad). Está pensada como barra horizontal fija que ocupa todo el ancho.【F:src/components/TopBar.tsx†L1-L123】
- **ResourceExplorer** (`src/components/ResourceExplorer.tsx`): panel lateral izquierdo de ancho fijo (~320px) con navegación jerárquica para presets y videos, búsqueda y drag & drop hacia la grilla.【F:src/components/ResourceExplorer.tsx†L1-L120】
- **LayerGrid** (`src/components/LayerGrid.tsx` + `LayerGrid.css`): vista principal dentro de `main-panel` que permite activar presets por capa, reaccionar a MIDI y administrar configuración de capas.【F:src/App.tsx†L1301-L1434】
- **Zona de contenido**: el `visual-stage` permanece en la sección central, mientras que el `controls-panel` fue reubicado dentro del `TaskActivityPanel` para imitar el panel de tareas/actividad de Proxmox.【F:src/App.tsx†L1406-L1510】【F:src/components/layout/ProxmoxLayout.css†L213-L320】
- **StatusBar** (`src/components/StatusBar.tsx`) se integra ahora dentro de `FooterPanel`, convirtiéndose en un footer plegable que emula el task log inferior.【F:src/App.tsx†L1512-L1609】【F:src/components/StatusBar.css†L1-L80】

### Observaciones de layout y estilo
- El layout actual está optimizado para emular Proxmox: sidebar fija, contenido central predominante, panel de tareas colapsable y footer plegable para estado/actividad.
- No existe un panel de chat ni una jerarquía de información similar a Proxmox; el foco visual está en la grilla y en el canvas.
- La paleta actual es predominantemente negra con acentos ámbar (`--accent-color: #FFB74D`) y tipografía `Segoe UI`/sans-serif.【F:src/App.css†L1-L20】
- El `workspace` ocupa todo el alto restante entre TopBar y StatusBar; el panel inferior comparte altura con la zona de visuales (no es un footer fijo).
- No hay sidebar secundaria ni breadcrumbs; la interacción depende de modales (`GlobalSettingsModal`, `ResourcesModal`) para configuraciones avanzadas.

## 2. Investigación y referencias de la UI de Proxmox

### Rasgos visuales y de layout
- Barra superior gris oscura con título, árbol de navegación y acciones contextuales alineadas a la derecha.
- Sidebar izquierda fija con estructura en árbol (datacenter, nodos, recursos), íconos sutiles y estados activos resaltados en gris claro.
- Área de contenido principal con pestañas horizontales en la parte superior, encabezados secundarios y paneles con bordes claros sobre fondo gris medio.
- Panel inferior de tareas/`Task Log` desacoplado que muestra actividad reciente; puede expandirse o plegarse.

### Elementos clave a replicar/adaptar
- **Sidebar**: debe agrupar recursos (agentes, configuraciones, preferencias, API keys) en una jerarquía similar al árbol de Proxmox, con indicadores de selección y estados hover planos.
- **Header**: incorporar un top bar consistente que permita colocar breadcrumbs/títulos y acciones rápidas; menos iconografía emoji y más botones planos.
- **Contenido principal**: reorganizar para priorizar un panel de chat central estilo tarjeta/tab, con pestañas o secciones para diferentes vistas si se requieren (p. ej. historial, configuración del chat).
- **Panel inferior**: zona dedicada a tasks/actividad inspirada en el `Task Log`, posiblemente colapsable, con tabla o lista de eventos.
- **Paleta y tipografía**: predominio de grises (fondo #f0f0f0/#2c3034) con acentos naranja (#d35400) y tipografía sans-serif limpia (Open Sans/Ubuntu).

### Gap analysis inicial
- El layout actual requiere una reestructuración completa: pasar de enfoque audiovisual de tres paneles a esquema “sidebar + contenido + task log”.
- Los componentes existentes (LayerGrid, ResourceExplorer, Visual stage) no son reutilizables en la nueva UI; habrá que introducir nuevos componentes para chat, sidebar de agentes y panel de actividad.
- Será necesario revisar rutas/estado global para manejar navegación tipo árbol o tabs, y definir un sistema de diseño coherente (tokens de color, tipografía, tamaños) alineado con Proxmox.

