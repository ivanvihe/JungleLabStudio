# UI Redesign Audit: Steps 1-10

## 1. Auditoría de la UI actual

### Arquitectura general
- `src/App.tsx` orquesta la aplicación completa y monta la estructura principal del layout, combinando barra superior, explorador lateral, grilla de capas y paneles inferiores.【F:src/App.tsx†L1261-L1479】
- Los estilos de layout se concentran en `src/AppLayout.css`, donde se define una estructura basada en flexbox con contenedor principal en columna, workspace dividido en panel lateral (`ResourceExplorer`) y panel central (`main-panel`), además de un bloque inferior para visuales y controles.【F:src/AppLayout.css†L1-L86】

### Componentes principales
- **TopBar** (`src/components/TopBar.tsx`): barra superior con secciones para estado MIDI, BPM, audio y controles rápidos (recursos, limpiar, ocultar UI, fullscreen, settings, Launchpad). Está pensada como barra horizontal fija que ocupa todo el ancho.【F:src/components/TopBar.tsx†L1-L123】
- **ResourceExplorer** (`src/components/ResourceExplorer.tsx`): panel lateral izquierdo de ancho fijo (~320px) con navegación jerárquica para presets y videos, búsqueda y drag & drop hacia la grilla.【F:src/components/ResourceExplorer.tsx†L1-L120】
- **LayerGrid** (`src/components/LayerGrid.tsx` + `LayerGrid.css`): vista principal dentro de `main-panel` que permite activar presets por capa, reaccionar a MIDI y administrar configuración de capas.【F:src/App.tsx†L1301-L1434】
- **Zona inferior**: se divide entre un `visual-stage` con el canvas principal y un `controls-panel` con tabs de controles (`VideoControls`, `PresetControls`). Usa scroll independiente y estilos de panel flotante oscuro.【F:src/App.tsx†L1446-L1479】【F:src/AppLayout.css†L56-L110】
- **StatusBar** (`src/components/StatusBar.tsx`) se monta fuera del fragmento mostrado pero añade otra barra inferior con métricas del engine.

### Observaciones de layout y estilo
- El layout actual está optimizado para una app audiovisual: visual central prominente, panel de controles derecho, navegación de recursos izquierda y barra superior cargada de indicadores.
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

## 3. Definición de arquitectura del layout

1. Bosquejar en Figma (o herramienta equivalente) la estructura `Sidebar` + `Header` + `MainChat` + `TaskActivityPanel`, incorporando tamaños aproximados (sidebar 280px, header 56px, panel inferior 220px).
2. Traducir el blueprint a componentes React vacíos (`Sidebar.tsx`, `MainChat.tsx`, `TaskActivityPanel.tsx`, `ShellLayout.tsx`) ubicados en `src/components/proxmox-clone/`.
3. Configurar el contenedor principal (`ShellLayout`) con CSS Grid/Flex para asegurar que el sidebar quede fijo y el panel inferior pueda colapsar.
4. Declarar props iniciales (p. ej. `onSectionSelect`, `activeSection`, `tasks`, `activities`) para permitir integración progresiva.

## 4. Actualización de estilos globales

1. Crear un archivo `src/styles/proxmox-theme.css` con variables CSS (`--pve-bg`, `--pve-surface`, `--pve-border`, `--pve-accent`, `--pve-text-primary`).
2. Ajustar `App.css` o envolver la app con un proveedor de estilos para aplicar la nueva paleta y tipografía (`font-family: "Ubuntu", "Open Sans", sans-serif`).
3. Normalizar espaciados y bordes redondeados mínimos (2-4px) mediante utilidades reutilizables.
4. Definir tokens para estados (`--pve-hover`, `--pve-active`) que replican el look Proxmox y documentarlos en la hoja de estilos.

## 5. Implementación del Sidebar estilo Proxmox

1. Estructurar el componente `Sidebar` con secciones plegables: "Agentes", "Recursos", "Configuraciones", "Preferencias", "API Keys".
2. Implementar un árbol con niveles anidados usando datos mock (`sidebarSections`) y componentes `SidebarGroup`/`SidebarItem`.
3. Añadir iconografía minimalista (usar `lucide-react` o set existente) y estilos hover/seleccionado planos.
4. Incorporar lógica para mostrar la selección activa y emitir eventos al contenedor (`onSelect(sectionId)`).

## 6. Diseño del panel principal de chat

1. Crear `MainChat` con cabecera que muestre el agente activo, breadcrumbs tipo "Agentes > Nombre", y acciones (configuración, historial, clear chat).
2. Diseñar el área de mensajes con layout de columnas Proxmox (fondo gris claro, tarjetas con borde sutil, timestamps a la derecha).
3. Añadir input compuesto al pie del chat (campo de texto + botones enviar/adjuntar) siguiendo estilos planos.
4. Preparar tabs opcionales (`Tabs` para Chat / Contexto / Configuración) si se requieren vistas múltiples.

## 7. Zona inferior de tareas/actividad

1. Implementar `TaskActivityPanel` con tabs "Tareas" y "Actividad", inspirado en el `Task Log` de Proxmox.
2. Incluir tabla/lista con columnas: Estado, Descripción, Agente, Hora de inicio, Duración.
3. Añadir controles de colapsar/expandir y altura resizable (drag handle).
4. Preparar conexión con store global para recibir updates en tiempo real (placeholder con mock data mientras tanto).

## 8. Ajustes de responsividad y usabilidad

1. Definir breakpoints clave (≥1280px desktop completo, 1024px tablets, <768px vista compacta).
2. Hacer que el sidebar pueda colapsar a íconos en pantallas medianas y ocultarse en móviles mediante botón en el header.
3. Asegurar que el panel inferior se transforme en pestaña flotante en móviles (overlay sobre el chat).
4. Probar con `prefers-reduced-motion` y teclas de navegación (focus visible) para accesibilidad.

## 9. Refactorización y limpieza

1. Extraer componentes utilitarios (`Panel`, `SectionHeader`, `InfoBadge`) para evitar duplicación.
2. Mover estilos compartidos a `src/styles/proxmox-theme.css` y eliminar CSS legacy que ya no se usa.
3. Actualizar imports y rutas para remover referencias a layout audiovisual si ya no se utilizan.
4. Escribir documentación breve en `docs/proxmox-clone-guidelines.md` sobre el nuevo sistema de diseño.

## 10. Pruebas y validación

1. Crear checklist visual (capturas comparativas Proxmox vs clone) y validarla con stakeholders.
2. Ejecutar pruebas unitarias/componentes (`npm run test`, `npm run lint`) asegurando que el layout nuevo no rompe lógica existente.
3. Añadir pruebas E2E/manuales para rutas clave: selección de agente, envío de mensaje, revisión de actividad.
4. Recoger feedback y registrar ajustes pendientes en el backlog antes de cerrar la fase.

