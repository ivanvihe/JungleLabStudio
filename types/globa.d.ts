// types/global.d.ts
interface Window {
  __TAURI__?: any;
  electronAPI?: {
    applySettings: (settings: { maximize?: boolean; monitorId?: number }) => void;
    getDisplays: () => Promise<{ id: number; label: string; bounds: { x: number; y: number; width: number; height: number }; scaleFactor: number; primary: boolean; }[]>;
    toggleFullscreen: (ids: number[]) => Promise<void>;
    readTextFile: (path: string) => Promise<string>;
    writeTextFile: (path: string, data: string) => Promise<void>;
    exists: (path: string) => Promise<boolean>;
  };
}

// Declaración de módulo para evitar errores de TypeScript
declare module '@tauri-apps/api/event' {
  export function listen(event: string, handler: (event: any) => void): Promise<() => void>;
}