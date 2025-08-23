import React, { useState, useEffect } from 'react';

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  isPrimary: boolean;
  scaleFactor: number;
}

interface SystemSettingsProps {
  startMaximized: boolean;
  onStartMaximizedChange: (value: boolean) => void;
  monitors: MonitorInfo[];
  startMonitor: string | null;
  onStartMonitorChange: (id: string | null) => void;
  sidebarCollapsed: boolean;
  onSidebarCollapsedChange: (value: boolean) => void;
}

export const SystemSettings: React.FC<SystemSettingsProps> = ({
  startMaximized,
  onStartMaximizedChange,
  monitors,
  startMonitor,
  onStartMonitorChange,
  sidebarCollapsed,
  onSidebarCollapsedChange,
}) => {
  const [autoCleanCache, setAutoCleanCache] = useState(() =>
    localStorage.getItem('autoCleanCache') !== 'false'
  );
  const [memoryLimit, setMemoryLimit] = useState(() =>
    parseInt(localStorage.getItem('memoryLimit') || '512')
  );
  const [webglSupport, setWebglSupport] = useState<string>('Detectando...');

  useEffect(() => {
    localStorage.setItem('autoCleanCache', autoCleanCache.toString());
  }, [autoCleanCache]);

  useEffect(() => {
    localStorage.setItem('memoryLimit', memoryLimit.toString());
  }, [memoryLimit]);

  useEffect(() => {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const loseContext = gl.getExtension('WEBGL_lose_context');
      if (loseContext) {
        loseContext.loseContext();
      }
      setWebglSupport('Disponible');
    } else {
      setWebglSupport('No disponible');
    }
  }, []);

  const handleClearCache = () => {
    const keysToKeep = [
      'selectedAudioDevice',
      'selectedMidiDevice',
      'monitorRoles',
      'glitchTextPads',
      'targetFPS',
      'vsync',
      'antialias',
      'pixelRatio',
      'visualScale',
      'preferredGPU',
      'audioBufferSize',
      'fftSize',
      'audioSmoothing',
      'autoCleanCache',
      'memoryLimit',
    ];

    Object.keys(localStorage).forEach((key) => {
      if (!keysToKeep.includes(key)) {
        localStorage.removeItem(key);
      }
    });

    if ('gc' in window) {
      (window as any).gc();
    }

    alert('Cache limpiado exitosamente');
  };

  const handleResetSettings = () => {
    if (confirm('¿Estás seguro de que quieres restablecer todas las configuraciones?')) {
      localStorage.clear();
      window.location.reload();
    }
  };

  const getMemoryUsage = () => {
    if ('memory' in performance) {
      const mem = (performance as any).memory;
      return {
        used: Math.round(mem.usedJSHeapSize / 1048576),
        total: Math.round(mem.totalJSHeapSize / 1048576),
        limit: Math.round(mem.jsHeapSizeLimit / 1048576),
      };
    }
    return null;
  };

  const memInfo = getMemoryUsage();

  return (
    <div className="settings-section">
      <h3>🔧 Sistema y Mantenimiento</h3>

      <div className="setting-group">
        <label className="setting-checkbox">
          <input
            type="checkbox"
            checked={startMaximized}
            onChange={(e) => onStartMaximizedChange(e.target.checked)}
          />
          <span>Iniciar maximizada</span>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Monitor de inicio</span>
          <select
            value={startMonitor || ''}
            onChange={(e) => onStartMonitorChange(e.target.value || null)}
            className="setting-select"
          >
            <option value="">Monitor principal</option>
            {monitors.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-checkbox">
          <input
            type="checkbox"
            checked={sidebarCollapsed}
            onChange={(e) => onSidebarCollapsedChange(e.target.checked)}
          />
          <span>Plegar sidebar al iniciar</span>
        </label>
      </div>

      {memInfo && (
        <div className="memory-usage">
          <h4>Uso de Memoria</h4>
          <div className="memory-bar">
            <div
              className="memory-fill"
              style={{ width: `${(memInfo.used / memInfo.limit) * 100}%` }}
            />
          </div>
          <span>
            {memInfo.used}MB de {memInfo.limit}MB usados
          </span>
        </div>
      )}

      <div className="setting-group">
        <label className="setting-label">
          <span>Límite de Memoria (MB): {memoryLimit}</span>
          <input
            type="range"
            min={256}
            max={2048}
            step={64}
            value={memoryLimit}
            onChange={(e) => setMemoryLimit(parseInt(e.target.value))}
            className="setting-slider"
          />
        </label>
        <small className="setting-hint">
          La aplicación intentará mantenerse bajo este límite
        </small>
      </div>

      <div className="setting-group">
        <label className="setting-checkbox">
          <input
            type="checkbox"
            checked={autoCleanCache}
            onChange={(e) => setAutoCleanCache(e.target.checked)}
          />
          <span>Limpieza Automática de Cache</span>
        </label>
        <small className="setting-hint">Limpia automáticamente recursos no utilizados</small>
      </div>

      <div className="action-buttons">
        <button
          className="action-button clear-button"
          onClick={handleClearCache}
        >
          🧹 Limpiar Cache
        </button>

        <button
          className="action-button reset-button"
          onClick={handleResetSettings}
        >
          ⚠️ Restablecer Todo
        </button>
      </div>

      <div className="system-details">
        <h4>Información Técnica</h4>
        <div className="tech-info">
          <div className="tech-item">
            <span>User Agent:</span>
            <span className="tech-value">
              {navigator.userAgent.split(' ').slice(-2).join(' ')}
            </span>
          </div>
          <div className="tech-item">
            <span>WebGL:</span>
            <span className="tech-value">{webglSupport}</span>
          </div>
          <div className="tech-item">
            <span>Audio Context:</span>
            <span className="tech-value">
              {window.AudioContext || (window as any).webkitAudioContext
                ? 'Disponible'
                : 'No disponible'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

