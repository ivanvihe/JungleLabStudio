import React, { useState, useEffect } from 'react';

export const VideoSettings: React.FC = () => {
  const [targetFPS, setTargetFPS] = useState(() =>
    parseInt(localStorage.getItem('targetFPS') || '60')
  );
  const [vsync, setVsync] = useState(
    () => localStorage.getItem('vsync') !== 'false'
  );
  const [antialias, setAntialias] = useState(
    () => localStorage.getItem('antialias') !== 'false'
  );
  const [pixelRatio, setPixelRatio] = useState(() =>
    parseFloat(localStorage.getItem('pixelRatio') || '1')
  );
  const [visualScale, setVisualScale] = useState(() =>
    parseFloat(localStorage.getItem('visualScale') || '1')
  );
  const [preferredGPU, setPreferredGPU] = useState(
    () => localStorage.getItem('preferredGPU') || 'high-performance'
  );
  const [gpuInfo, setGpuInfo] = useState<string>('Detectando...');

  useEffect(() => {
    localStorage.setItem('targetFPS', targetFPS.toString());
  }, [targetFPS]);
  useEffect(() => {
    localStorage.setItem('vsync', vsync.toString());
  }, [vsync]);
  useEffect(() => {
    localStorage.setItem('antialias', antialias.toString());
  }, [antialias]);
  useEffect(() => {
    localStorage.setItem('pixelRatio', pixelRatio.toString());
  }, [pixelRatio]);
  useEffect(() => {
    localStorage.setItem('visualScale', visualScale.toString());
    window.dispatchEvent(new Event('resize'));
  }, [visualScale]);
  useEffect(() => {
    localStorage.setItem('preferredGPU', preferredGPU);
  }, [preferredGPU]);

  useEffect(() => {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        setGpuInfo(gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL));
      } else {
        setGpuInfo('Información no disponible');
      }
      const loseContext = gl.getExtension('WEBGL_lose_context');
      if (loseContext) {
        loseContext.loseContext();
      }
    } else {
      setGpuInfo('No disponible');
    }
  }, []);

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
      <h3>🎮 Rendimiento y Gráficos</h3>

      <div className="system-info">
        <h4>Información del Sistema</h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">GPU:</span>
            <span className="info-value">{gpuInfo}</span>
          </div>
          {memInfo && (
            <div className="info-item">
              <span className="info-label">Memoria:</span>
              <span className="info-value">
                {memInfo.used}MB / {memInfo.limit}MB
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Preferencia de GPU</span>
          <select
            value={preferredGPU}
            onChange={(e) => setPreferredGPU(e.target.value)}
            className="setting-select"
          >
            <option value="default">Por Defecto</option>
            <option value="high-performance">Alto Rendimiento</option>
            <option value="low-power">Bajo Consumo</option>
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>FPS Objetivo: {targetFPS}</span>
          <input
            type="range"
            min={30}
            max={144}
            step={1}
            value={targetFPS}
            onChange={(e) => setTargetFPS(parseInt(e.target.value))}
            className="setting-slider"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Ratio de Píxeles: {pixelRatio}x</span>
          <input
            type="range"
            min={0.5}
            max={2}
            step={0.1}
            value={pixelRatio}
            onChange={(e) => setPixelRatio(parseFloat(e.target.value))}
            className="setting-slider"
          />
        </label>
        <small className="setting-hint">Menor = mejor rendimiento, Mayor = mejor calidad</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Escala de Pantalla: {(visualScale * 100).toFixed(0)}%</span>
          <input
            type="range"
            min={0.5}
            max={1}
            step={0.05}
            value={visualScale}
            onChange={(e) => setVisualScale(parseFloat(e.target.value))}
            className="setting-slider"
          />
        </label>
        <small className="setting-hint">Ajusta cuánto de la pantalla ocupa el lienzo</small>
      </div>

      <div className="setting-group">
        <label className="setting-checkbox">
          <input
            type="checkbox"
            checked={vsync}
            onChange={(e) => setVsync(e.target.checked)}
          />
          <span>Activar V-Sync</span>
        </label>
        <small className="setting-hint">Sincroniza con la frecuencia del monitor</small>
      </div>

      <div className="setting-group">
        <label className="setting-checkbox">
          <input
            type="checkbox"
            checked={antialias}
            onChange={(e) => setAntialias(e.target.checked)}
          />
          <span>Anti-aliasing</span>
        </label>
        <small className="setting-hint">Suaviza los bordes (impacto en rendimiento)</small>
      </div>
    </div>
  );
};

