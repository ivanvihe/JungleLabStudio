// MEJORA 2: App.tsx con detección de monitores mejorada

import React, { useEffect, useRef, useState } from 'react';
import { AudioVisualizerEngine } from './core/AudioVisualizerEngine';
import { LayerGrid } from './components/LayerGrid';
import { StatusBar } from './components/StatusBar';
import { PresetControls } from './components/PresetControls';
import { TopBar } from './components/TopBar';
import { GlobalSettingsModal } from './components/GlobalSettingsModal';
import { LoadedPreset, AudioData } from './core/PresetLoader';
import './App.css';
import './components/LayerGrid.css';

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  isPrimary: boolean;
  scaleFactor: number;
}

const App: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<AudioVisualizerEngine | null>(null);
  const clockTimesRef = useRef<number[]>([]);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [availablePresets, setAvailablePresets] = useState<LoadedPreset[]>([]);
  const [audioData, setAudioData] = useState<AudioData>({ low: 0, mid: 0, high: 0, fft: [] });
  const [fps, setFps] = useState(60);
  const [status, setStatus] = useState('Inicializando...');
  const [activeLayers, setActiveLayers] = useState<Record<string, string>>({});
  const [selectedPreset, setSelectedPreset] = useState<LoadedPreset | null>(null);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
  const [isControlsOpen, setIsControlsOpen] = useState(true);

  // Top bar & settings state
  const [midiDevices, setMidiDevices] = useState<any[]>([]);
  const [midiDeviceId, setMidiDeviceId] = useState<string | null>(null);
  const [midiActive, setMidiActive] = useState(false);
  const [bpm, setBpm] = useState<number | null>(null);
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [audioDeviceId, setAudioDeviceId] = useState<string | null>(null);
  const [audioGain, setAudioGain] = useState(1);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [monitors, setMonitors] = useState<MonitorInfo[]>([]);
  const [selectedMonitors, setSelectedMonitors] = useState<string[]>([]);
  const [glitchTextPads, setGlitchTextPads] = useState<number>(() => parseInt(localStorage.getItem('glitchTextPads') || '1'));
  const isFullscreenMode = new URLSearchParams(window.location.search).get('fullscreen') === 'true';

  // Persist selected devices across sessions
  useEffect(() => {
    const savedAudio = localStorage.getItem('selectedAudioDevice');
    const savedMidi = localStorage.getItem('selectedMidiDevice');
    const savedMonitors = localStorage.getItem('selectedMonitors');
    
    if (savedAudio) setAudioDeviceId(savedAudio);
    if (savedMidi) setMidiDeviceId(savedMidi);
    if (savedMonitors) {
      try {
        setSelectedMonitors(JSON.parse(savedMonitors));
      } catch (e) {
        console.warn('Error parsing saved monitors:', e);
      }
    }
  }, []);

  // Persist selected monitors
  useEffect(() => {
    localStorage.setItem('selectedMonitors', JSON.stringify(selectedMonitors));
  }, [selectedMonitors]);

  // Enumerar monitores disponibles con detección mejorada
  useEffect(() => {
    const loadMonitors = async () => {
      if ((window as any).__TAURI__) {
        try {
          // Load Tauri window API dynamically
          const { availableMonitors, currentMonitor } = await import(
            /* @vite-ignore */ '@tauri-apps/api/window'
          );
          
          const [mons, current] = await Promise.all([
            availableMonitors(),
            currentMonitor()
          ]);
          
          const mapped: MonitorInfo[] = mons.map((m, idx) => ({
            id: m.name || `monitor-${idx}`,
            label: `${m.name || `Monitor ${idx + 1}`} (${m.size.width}x${m.size.height})`,
            position: { x: m.position.x, y: m.position.y },
            size: { width: m.size.width, height: m.size.height },
            isPrimary: current ? (m.name === current.name) : idx === 0,
            scaleFactor: m.scaleFactor || 1
          }));
          
          // Ordenar: primario primero, luego por posición X
          mapped.sort((a, b) => {
            if (a.isPrimary !== b.isPrimary) return a.isPrimary ? -1 : 1;
            return a.position.x - b.position.x;
          });
          
          setMonitors(mapped);
          
          // Auto-seleccionar monitor primario si no hay selección previa
          if (selectedMonitors.length === 0) {
            const primaryMonitor = mapped.find(m => m.isPrimary);
            if (primaryMonitor) {
              setSelectedMonitors([primaryMonitor.id]);
            }
          }
          
          console.log(`🖥️ Detectados ${mapped.length} monitores:`, mapped);
        } catch (err) {
          console.warn('Monitor enumeration failed:', err);
          await loadFallbackMonitors();
        }
      } else {
        await loadFallbackMonitors();
      }
    };

    const loadFallbackMonitors = async () => {
      // Fallback para navegadores web - usar Screen API si está disponible
      const fallbackMonitors: MonitorInfo[] = [];
      
      if ('getScreenDetails' in window) {
        try {
          // @ts-ignore - Screen API experimental
          const screenDetails = await window.getScreenDetails();
          screenDetails.screens.forEach((screen: any, idx: number) => {
            fallbackMonitors.push({
              id: `screen-${idx}`,
              label: `Monitor ${idx + 1} (${screen.width}x${screen.height})`,
              position: { x: screen.left, y: screen.top },
              size: { width: screen.width, height: screen.height },
              isPrimary: screen.isPrimary || idx === 0,
              scaleFactor: screen.devicePixelRatio || 1
            });
          });
        } catch (e) {
          console.warn('Screen API failed:', e);
        }
      }
      
      // Si no se detectaron monitores, usar fallback básico
      if (fallbackMonitors.length === 0) {
        const fallback: MonitorInfo = {
          id: 'primary',
          label: `Monitor Principal (${window.screen.width}x${window.screen.height})`,
          position: { x: 0, y: 0 },
          size: { width: window.screen.width, height: window.screen.height },
          isPrimary: true,
          scaleFactor: window.devicePixelRatio || 1
        };
        fallbackMonitors.push(fallback);
      }
      
      setMonitors(fallbackMonitors);
      setSelectedMonitors([fallbackMonitors[0].id]);
    };

    loadMonitors();
  }, []);

  // ... resto del código existente ...

  const handleFullScreen = async () => {
    if ((window as any).__TAURI__) {
      // Guardar estado de capas activas
      localStorage.setItem('activeLayers', JSON.stringify(activeLayers));
      
      try {
        // Dynamically load the WebviewWindow constructor
        const { WebviewWindow } = await import(
          /* @vite-ignore */ '@tauri-apps/api/window'
        );
        
        const selectedMonitorsList = monitors.filter(m => selectedMonitors.includes(m.id));
        
        if (selectedMonitorsList.length === 0) {
          setStatus('Error: No hay monitores seleccionados');
          return;
        }
        
        console.log(`🎯 Abriendo fullscreen en ${selectedMonitorsList.length} monitores`);
        
        // Crear ventana para cada monitor seleccionado
        selectedMonitorsList.forEach((monitor, index) => {
          const label = `fullscreen-${monitor.id}-${Date.now()}-${index}`;
          
          const windowOptions = {
            url: `index.html?fullscreen=true&monitor=${monitor.id}`,
            x: monitor.position.x,
            y: monitor.position.y,
            width: monitor.size.width,
            height: monitor.size.height,
            decorations: false,
            fullscreen: true,
            skipTaskbar: true,
            resizable: false,
            title: `Visual Output - ${monitor.label}`,
            alwaysOnTop: false
          };
          
          console.log(`🖥️ Creando ventana en ${monitor.label}:`, windowOptions);
          
          try {
            new WebviewWindow(label, windowOptions);
          } catch (windowError) {
            console.error(`Error creando ventana para ${monitor.label}:`, windowError);
            setStatus(`Error: No se pudo crear ventana en ${monitor.label}`);
          }
        });
        
        setStatus(`Fullscreen activo en ${selectedMonitorsList.length} monitor(es)`);
      } catch (err) {
        console.error('Error en fullscreen:', err);
        setStatus('Error: No se pudo activar fullscreen');
      }
    } else {
      // Fallback para navegador web
      const elem: any = document.documentElement;
      if (elem.requestFullscreen) {
        await elem.requestFullscreen();
        setStatus('Fullscreen activado (navegador)');
      } else {
        setStatus('Error: Fullscreen no disponible');
      }
    }
  };

  const handleClearAll = () => {
    if (!engineRef.current) return;
    Object.keys(activeLayers).forEach(layerId => engineRef.current?.deactivateLayerPreset(layerId));
    setActiveLayers({});
    setStatus('Capas limpiadas');
  };

  const handleToggleMonitor = (id: string) => {
    setSelectedMonitors(prev => {
      const newSelection = prev.includes(id) 
        ? prev.filter(m => m !== id) 
        : [...prev, id];
      
      // Asegurar que al menos un monitor esté seleccionado
      if (newSelection.length === 0) {
        const primaryMonitor = monitors.find(m => m.isPrimary);
        return primaryMonitor ? [primaryMonitor.id] : [monitors[0]?.id].filter(Boolean);
      }
      
      return newSelection;
    });
  };

  // ... resto del código existente ...

  const getCurrentPresetName = (): string => {
    if (!selectedPreset) return 'Ninguno';
    return `${selectedPreset.config.name} (${selectedLayer || 'N/A'})`;
  };

  const midiDeviceName = midiDeviceId ? midiDevices.find((d: any) => d.id === midiDeviceId)?.name || null : null;
  const audioDeviceName = audioDeviceId ? audioDevices.find(d => d.deviceId === audioDeviceId)?.label || null : null;
  const audioLevel = Math.min((audioData.low + audioData.mid + audioData.high) / 3, 1);

  return isFullscreenMode ? (
    <div className="app fullscreen-mode">
      <canvas ref={canvasRef} className="main-canvas" />
    </div>
  ) : (
    <div className="app">
      <TopBar
        midiActive={midiActive}
        midiDeviceName={midiDeviceName}
        midiDeviceCount={midiDevices.length}
        bpm={bpm}
        audioDeviceName={audioDeviceName}
        audioDeviceCount={audioDevices.length}
        audioGain={audioGain}
        onAudioGainChange={setAudioGain}
        audioLevel={audioLevel}
        onFullScreen={handleFullScreen}
        onClearAll={handleClearAll}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Grid de capas */}
      <div className="layer-grid-container">
        <LayerGrid
          presets={availablePresets}
          onPresetActivate={(layerId, presetId) => {
            // MEJORA 3: Asegurar independencia entre layers
            if (engineRef.current) {
              engineRef.current.activateLayerPreset(layerId, presetId);
              setActiveLayers(prev => ({ ...prev, [layerId]: presetId }));
              
              // Encontrar y seleccionar el preset para mostrar controles
              const preset = availablePresets.find(p => p.id === presetId);
              if (preset) {
                setSelectedPreset(preset);
                setSelectedLayer(layerId);
              }
            }
          }}
          onLayerClear={(layerId) => {
            if (engineRef.current) {
              engineRef.current.deactivateLayerPreset(layerId);
              setActiveLayers(prev => {
                const newLayers = { ...prev };
                delete newLayers[layerId];
                return newLayers;
              });
              
              // Limpiar selección si se limpia el layer seleccionado
              if (selectedLayer === layerId) {
                setSelectedPreset(null);
                setSelectedLayer(null);
              }
            }
          }}
          onLayerConfigChange={(layerId, config) => {
            if (engineRef.current) {
              engineRef.current.updateLayerConfig(layerId, config);
            }
          }}
        />
      </div>

      {/* Sección inferior con visuales y controles */}
      <div className="bottom-section">
        <canvas ref={canvasRef} className="main-canvas" />
        <div className={`controls-panel ${isControlsOpen ? '' : 'collapsed'}`}>
          <button
            className="toggle-sidebar"
            onClick={() => setIsControlsOpen(!isControlsOpen)}
          >
            {isControlsOpen ? '>' : '<'}
          </button>
          {isControlsOpen && selectedPreset && (
            <PresetControls
              preset={selectedPreset}
              onConfigUpdate={(config) => {
                if (engineRef.current && selectedLayer) {
                  engineRef.current.updateLayerPresetConfig(selectedLayer, config);
                }
              }}
            />
          )}
          {isControlsOpen && !selectedPreset && (
            <div className="no-preset-selected">Selecciona un preset</div>
          )}
        </div>
      </div>

      {/* Barra de estado */}
      <StatusBar
        status={status}
        fps={fps}
        currentPreset={getCurrentPresetName()}
        audioData={audioData}
      />

      <GlobalSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        audioDevices={audioDevices.map(d => ({ id: d.deviceId, label: d.label || d.deviceId }))}
        midiDevices={midiDevices.map((d: any) => ({ id: d.id, label: d.name || d.id }))}
        selectedAudioId={audioDeviceId}
        selectedMidiId={midiDeviceId}
        onSelectAudio={(id) => {
          setAudioDeviceId(id || null);
          if (id) {
            localStorage.setItem('selectedAudioDevice', id);
          } else {
            localStorage.removeItem('selectedAudioDevice');
          }
        }}
        onSelectMidi={(id) => {
          setMidiDeviceId(id || null);
          if (id) {
            localStorage.setItem('selectedMidiDevice', id);
          } else {
            localStorage.removeItem('selectedMidiDevice');
          }
        }}
        audioGain={audioGain}
        onAudioGainChange={setAudioGain}
        monitors={monitors}
        selectedMonitors={selectedMonitors}
        onToggleMonitor={handleToggleMonitor}
        glitchTextPads={glitchTextPads}
        onGlitchPadChange={async (value: number) => {
          setGlitchTextPads(value);
          localStorage.setItem('glitchTextPads', value.toString());
          if (engineRef.current) {
            const presets = await engineRef.current.updateGlitchPadCount(value);
            setAvailablePresets(presets);
          }
        }}
      />
    </div>
  );
};

export default App;