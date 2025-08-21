// MEJORA 4: GlobalSettingsModal.tsx completamente rediseñado

import React, { useState, useEffect } from 'react';
import './GlobalSettingsModal.css';  // ✅ AÑADIR ESTE IMPORT

interface DeviceOption {
  id: string;
  label: string;
}

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  isPrimary: boolean;
  scaleFactor: number;
}

interface GlobalSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  audioDevices: DeviceOption[];
  midiDevices: DeviceOption[];
  selectedAudioId: string | null;
  selectedMidiId: string | null;
  onSelectAudio: (id: string) => void;
  onSelectMidi: (id: string) => void;
  audioGain: number;
  onAudioGainChange: (value: number) => void;
  midiClockDelay: number;
  onMidiClockDelayChange: (value: number) => void;
  midiClockType: string;
  onMidiClockTypeChange: (value: string) => void;
  layerChannels: Record<string, number>;
  onLayerChannelChange: (layerId: string, channel: number) => void;
  monitors: MonitorInfo[];
  selectedMonitors: string[];
  fullscreenMainMonitor: string | null;
  onFullscreenMainMonitorChange: (id: string | null) => void;
  onToggleMonitor: (id: string) => void;
  startMonitor: string | null;
  onStartMonitorChange: (id: string | null) => void;
  glitchTextPads: number;
  onGlitchPadChange: (value: number) => void;
  hideUiHotkey: string;
  onHideUiHotkeyChange: (value: string) => void;
  fullscreenHotkey: string;
  onFullscreenHotkeyChange: (value: string) => void;
  exitFullscreenHotkey: string;
  onExitFullscreenHotkeyChange: (value: string) => void;
  fullscreenByDefault: boolean;
  onFullscreenByDefaultChange: (value: boolean) => void;
  startMaximized: boolean;
  onStartMaximizedChange: (value: boolean) => void;
  sidebarCollapsed: boolean;
  onSidebarCollapsedChange: (value: boolean) => void;
}

export const GlobalSettingsModal: React.FC<GlobalSettingsModalProps> = ({
  isOpen,
  onClose,
  audioDevices,
  midiDevices,
  selectedAudioId,
  selectedMidiId,
  onSelectAudio,
  onSelectMidi,
  audioGain,
  onAudioGainChange,
  midiClockDelay,
  onMidiClockDelayChange,
  midiClockType,
  onMidiClockTypeChange,
  layerChannels,
  onLayerChannelChange,
  monitors,
  selectedMonitors,
  fullscreenMainMonitor,
  onFullscreenMainMonitorChange,
  onToggleMonitor,
  startMonitor,
  onStartMonitorChange,
  glitchTextPads,
  onGlitchPadChange,
  hideUiHotkey,
  onHideUiHotkeyChange,
  fullscreenHotkey,
  onFullscreenHotkeyChange,
  exitFullscreenHotkey,
  onExitFullscreenHotkeyChange,
  fullscreenByDefault,
  onFullscreenByDefaultChange,
  startMaximized,
  onStartMaximizedChange,
  sidebarCollapsed,
  onSidebarCollapsedChange
}) => {
  const [activeTab, setActiveTab] = useState('audio');
  
  // Settings adicionales
  const [targetFPS, setTargetFPS] = useState(() => parseInt(localStorage.getItem('targetFPS') || '60'));
  const [vsync, setVsync] = useState(() => localStorage.getItem('vsync') !== 'false');
  const [antialias, setAntialias] = useState(() => localStorage.getItem('antialias') !== 'false');
  const [pixelRatio, setPixelRatio] = useState(() => parseFloat(localStorage.getItem('pixelRatio') || '1'));
  const [preferredGPU, setPreferredGPU] = useState(() => localStorage.getItem('preferredGPU') || 'high-performance');
  const [bufferSize, setBufferSize] = useState(() => parseInt(localStorage.getItem('audioBufferSize') || '2048'));
  const [fftSize, setFFTSize] = useState(() => parseInt(localStorage.getItem('fftSize') || '2048'));
  const [smoothingTime, setSmoothingTime] = useState(() => parseFloat(localStorage.getItem('audioSmoothing') || '0.8'));
  const [autoCleanCache, setAutoCleanCache] = useState(() => localStorage.getItem('autoCleanCache') !== 'false');
  const [memoryLimit, setMemoryLimit] = useState(() => parseInt(localStorage.getItem('memoryLimit') || '512'));

  // Guardar configuraciones
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
    localStorage.setItem('preferredGPU', preferredGPU);
  }, [preferredGPU]);

  useEffect(() => {
    localStorage.setItem('audioBufferSize', bufferSize.toString());
  }, [bufferSize]);

  useEffect(() => {
    localStorage.setItem('fftSize', fftSize.toString());
  }, [fftSize]);

  useEffect(() => {
    localStorage.setItem('audioSmoothing', smoothingTime.toString());
  }, [smoothingTime]);

  useEffect(() => {
    localStorage.setItem('autoCleanCache', autoCleanCache.toString());
  }, [autoCleanCache]);

  useEffect(() => {
    localStorage.setItem('memoryLimit', memoryLimit.toString());
  }, [memoryLimit]);

  const handleClearCache = () => {
    // Limpiar localStorage y sessionStorage
    const keysToKeep = [
      'selectedAudioDevice', 'selectedMidiDevice', 'selectedMonitors', 
      'glitchTextPads', 'targetFPS', 'vsync', 'antialias', 'pixelRatio',
      'preferredGPU', 'audioBufferSize', 'fftSize', 'audioSmoothing',
      'autoCleanCache', 'memoryLimit'
    ];
    
    Object.keys(localStorage).forEach(key => {
      if (!keysToKeep.includes(key)) {
        localStorage.removeItem(key);
      }
    });
    
    // Forzar garbage collection si está disponible
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

  const getGPUInfo = () => {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return 'No disponible';
    
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    if (debugInfo) {
      return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
    }
    return 'Información no disponible';
  };

  const getMemoryUsage = () => {
    if ('memory' in performance) {
      const mem = (performance as any).memory;
      return {
        used: Math.round(mem.usedJSHeapSize / 1048576),
        total: Math.round(mem.totalJSHeapSize / 1048576),
        limit: Math.round(mem.jsHeapSizeLimit / 1048576)
      };
    }
    return null;
  };

  if (!isOpen) return null;

  const memInfo = getMemoryUsage();

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal-content">
        {/* Header */}
        <div className="settings-header">
          <h2>⚙️ Configuración Global</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        {/* Tabs */}
        <div className="settings-tabs">
          {[
            { id: 'audio', label: 'Audio', icon: '🎵' },
            { id: 'video', label: 'Rendimiento', icon: '🎮' },
            { id: 'fullscreen', label: 'Monitores', icon: '🖥️' },
            { id: 'visual', label: 'Visuales', icon: '🎨' },
            { id: 'system', label: 'Sistema', icon: '🔧' }
          ].map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="settings-content">
          {/* Audio Tab */}
          {activeTab === 'audio' && (
            <div className="settings-section">
              <h3>🎵 Configuración de Audio</h3>
              
              <div className="setting-group">
                <label className="setting-label">
                  <span>Dispositivo de Entrada</span>
                  <select
                    value={selectedAudioId || ''}
                    onChange={(e) => onSelectAudio(e.target.value)}
                    className="setting-select"
                  >
                    <option value="">Por Defecto</option>
                    {audioDevices.map(dev => (
                      <option key={dev.id} value={dev.id}>{dev.label}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Ganancia de Entrada: {(audioGain * 100).toFixed(0)}%</span>
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.01}
                    value={audioGain}
                    onChange={(e) => onAudioGainChange(parseFloat(e.target.value))}
                    className="setting-slider"
                  />
                </label>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Tamaño de Buffer</span>
                  <select
                    value={bufferSize}
                    onChange={(e) => setBufferSize(parseInt(e.target.value))}
                    className="setting-select"
                  >
                    <option value={512}>512 (Baja latencia)</option>
                    <option value={1024}>1024 (Balanceado)</option>
                    <option value={2048}>2048 (Recomendado)</option>
                    <option value={4096}>4096 (Alta estabilidad)</option>
                  </select>
                </label>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Resolución FFT</span>
                  <select
                    value={fftSize}
                    onChange={(e) => setFFTSize(parseInt(e.target.value))}
                    className="setting-select"
                  >
                    <option value={1024}>1024 (Rápido)</option>
                    <option value={2048}>2048 (Recomendado)</option>
                    <option value={4096}>4096 (Alta precisión)</option>
                    <option value={8192}>8192 (Máxima calidad)</option>
                  </select>
                </label>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Suavizado de Audio: {(smoothingTime * 100).toFixed(0)}%</span>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.01}
                    value={smoothingTime}
                    onChange={(e) => setSmoothingTime(parseFloat(e.target.value))}
                    className="setting-slider"
                  />
                </label>
              </div>

              <div className="setting-group">
                <h4>MIDI</h4>
                <label className="setting-label">
                  <span>Dispositivo MIDI</span>
                  <select
                    value={selectedMidiId || ''}
                    onChange={(e) => onSelectMidi(e.target.value)}
                    className="setting-select"
                  >
                    <option value="">Por Defecto</option>
                    {midiDevices.map(dev => (
                      <option key={dev.id} value={dev.id}>{dev.label}</option>
                    ))}
                  </select>
                </label>
                <label className="setting-label">
                  <span>Tipo de Clock</span>
                  <select
                    value={midiClockType}
                    onChange={(e) => onMidiClockTypeChange(e.target.value)}
                    className="setting-select"
                  >
                    <option value="midi">MIDI</option>
                    <option value="off">Off</option>
                  </select>
                </label>
                <label className="setting-label">
                  <span>Delay Clock (ms)</span>
                  <input
                    type="number"
                    min={0}
                    max={1000}
                    value={midiClockDelay}
                    onChange={(e) => onMidiClockDelayChange(parseInt(e.target.value) || 0)}
                    className="setting-number"
                  />
                </label>
                <div className="layer-channel-settings">
                  <h5>Canal MIDI por Layer</h5>
                  {['A','B','C'].map(id => (
                    <label key={id} className="setting-label">
                      <span>Layer {id}</span>
                      <input
                        type="number"
                        min={1}
                        max={16}
                        value={layerChannels[id]}
                        onChange={(e) => onLayerChannelChange(id, parseInt(e.target.value) || 1)}
                        className="setting-number"
                      />
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Video/Performance Tab */}
          {activeTab === 'video' && (
            <div className="settings-section">
              <h3>🎮 Rendimiento y Gráficos</h3>
              
              <div className="system-info">
                <h4>Información del Sistema</h4>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">GPU:</span>
                    <span className="info-value">{getGPUInfo()}</span>
                  </div>
                  {memInfo && (
                    <div className="info-item">
                      <span className="info-label">Memoria:</span>
                      <span className="info-value">{memInfo.used}MB / {memInfo.limit}MB</span>
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
          )}

          {/* Fullscreen/Monitors Tab */}
          {activeTab === 'fullscreen' && (
            <div className="settings-section">
              <h3>🖥️ Configuración de Monitores</h3>
              
              <div className="monitors-grid">
                {monitors.map(monitor => (
                  <div key={monitor.id} className="monitor-card">
                    <div className="monitor-preview">
                      <div className="monitor-screen">
                        <span className="monitor-resolution">
                          {monitor.size.width}×{monitor.size.height}
                        </span>
                        {monitor.isPrimary && (
                          <span className="primary-badge">Principal</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="monitor-info">
                      <h4>{monitor.label}</h4>
                      <div className="monitor-details">
                        <span>Posición: {monitor.position.x}, {monitor.position.y}</span>
                        <span>Escala: {monitor.scaleFactor}x</span>
                      </div>
                      
                      <label className="monitor-checkbox">
                        <input
                          type="checkbox"
                          checked={selectedMonitors.includes(monitor.id)}
                          onChange={() => onToggleMonitor(monitor.id)}
                        />
                        <span>Usar en Fullscreen</span>
                      </label>
                    </div>
                  </div>
                ))}
              </div>

              <div className="monitors-summary">
                <strong>Monitores seleccionados: {selectedMonitors.length}</strong>
                <p>Se abrirá una ventana fullscreen en cada monitor seleccionado</p>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Monitor principal en fullscreen</span>
                  <select
                    value={fullscreenMainMonitor || ''}
                    onChange={(e) => onFullscreenMainMonitorChange(e.target.value || null)}
                    className="setting-select"
                  >
                    <option value="">Primero de la lista</option>
                    {selectedMonitors.map(id => {
                      const m = monitors.find(mon => mon.id === id);
                      return (
                        <option key={id} value={id}>
                          {m?.label || id}
                        </option>
                      );
                    })}
                  </select>
                </label>
                <small className="setting-hint">La ventana principal permanecerá en este monitor</small>
              </div>
            </div>
          )}

          {/* Visual Settings Tab */}
          {activeTab === 'visual' && (
            <div className="settings-section">
              <h3>🎨 Configuración Visual</h3>
              <div className="setting-group">
                <label className="setting-label">
                  <span>Tecla para ocultar UI</span>
                  <input
                    type="text"
                    value={hideUiHotkey}
                    onKeyDown={(e) => {
                      e.preventDefault();
                      onHideUiHotkeyChange(e.key);
                    }}
                    className="setting-number"
                    readOnly
                  />
                </label>
                <small className="setting-hint">Presiona una tecla (por defecto F10)</small>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Tecla para fullscreen</span>
                  <input
                    type="text"
                    value={fullscreenHotkey}
                    onKeyDown={(e) => {
                      e.preventDefault();
                      onFullscreenHotkeyChange(e.key);
                    }}
                    className="setting-number"
                    readOnly
                  />
                </label>
                <small className="setting-hint">Presiona una tecla (por defecto F9)</small>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Tecla para salir de fullscreen</span>
                  <input
                    type="text"
                    value={exitFullscreenHotkey}
                    onKeyDown={(e) => {
                      e.preventDefault();
                      onExitFullscreenHotkeyChange(e.key);
                    }}
                    className="setting-number"
                    readOnly
                  />
                </label>
                <small className="setting-hint">Presiona una tecla (por defecto F11)</small>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <input
                    type="checkbox"
                    checked={fullscreenByDefault}
                    onChange={(e) => onFullscreenByDefaultChange(e.target.checked)}
                  />
                  <span>Ventanas en fullscreen por defecto</span>
                </label>
              </div>

              <div className="setting-group">
                <label className="setting-label">
                  <span>Pads de Texto Glitch: {glitchTextPads}</span>
                  <input
                    type="range"
                    min={1}
                    max={8}
                    step={1}
                    value={glitchTextPads}
                    onChange={(e) => onGlitchPadChange(parseInt(e.target.value))}
                    className="setting-slider"
                  />
                </label>
                <small className="setting-hint">Número de pads de texto disponibles en presets de glitch</small>
              </div>

              <div className="setting-group">
                <h4>Configuración de Layers</h4>
                <div className="layers-info">
                  <div className="layer-info">
                    <span className="layer-badge layer-c">C</span>
                    <span>Layer de Fondo - Renderiza primero</span>
                  </div>
                  <div className="layer-info">
                    <span className="layer-badge layer-b">B</span>
                    <span>Layer Medio - Mezcla con transparencia</span>
                  </div>
                  <div className="layer-info">
                    <span className="layer-badge layer-a">A</span>
                    <span>Layer Frontal - Renderiza encima</span>
                  </div>
                </div>
                <small className="setting-hint">
                  Todos los layers se mezclan con transparencia automática. Los presets mantienen fondos transparentes para permitir la composición correcta.
                </small>
              </div>

              <div className="setting-group">
                <h4>Calidad Visual</h4>
                <div className="quality-presets">
                  <button 
                    className="quality-button"
                    onClick={() => {
                      setPixelRatio(0.7);
                      setAntialias(false);
                      setTargetFPS(60);
                    }}
                  >
                    🏃 Rendimiento
                  </button>
                  <button 
                    className="quality-button"
                    onClick={() => {
                      setPixelRatio(1.0);
                      setAntialias(true);
                      setTargetFPS(60);
                    }}
                  >
                    ⚖️ Balanceado
                  </button>
                  <button 
                    className="quality-button"
                    onClick={() => {
                      setPixelRatio(1.5);
                      setAntialias(true);
                      setTargetFPS(120);
                    }}
                  >
                    💎 Calidad
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* System Tab */}
          {activeTab === 'system' && (
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
                    {monitors.map(m => (
                      <option key={m.id} value={m.id}>{m.label}</option>
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
                  <span>{memInfo.used}MB de {memInfo.limit}MB usados</span>
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
                <small className="setting-hint">La aplicación intentará mantenerse bajo este límite</small>
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
                    <span className="tech-value">{navigator.userAgent.split(' ').slice(-2).join(' ')}</span>
                  </div>
                  <div className="tech-item">
                    <span>WebGL:</span>
                    <span className="tech-value">
                      {(() => {
                        const canvas = document.createElement('canvas');
                        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
                        return gl ? 'Disponible' : 'No disponible';
                      })()}
                    </span>
                  </div>
                  <div className="tech-item">
                    <span>Audio Context:</span>
                    <span className="tech-value">
                      {window.AudioContext || (window as any).webkitAudioContext ? 'Disponible' : 'No disponible'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="settings-footer">
          <div className="settings-info">
            <span>💡 Los cambios se aplican automáticamente</span>
          </div>
          <button className="primary-button" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};