// types/global.d.ts
interface Window {
  __TAURI__?: any;
}

// Declaración de módulo para evitar errores de TypeScript
declare module '@tauri-apps/api/event' {
  export function listen(event: string, handler: (event: any) => void): Promise<() => void>;
}