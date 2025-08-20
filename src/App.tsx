import React, { useEffect, useRef, useState } from 'react';
import { AudioVisualizerEngine } from './core/AudioVisualizerEngine';
import { LayerGrid } from './components/LayerGrid';
import { StatusBar } from './components/StatusBar';
import { PresetControls } from './components/PresetControls';
import { TopBar } from './components/TopBar';
import { GlobalSettingsModal } from './components/GlobalSettingsModal';
import { LoadedPreset, AudioData } from './core/PresetLoader';
import { WebviewWindow, availableMonitors } from '@tauri-apps/api/window';
import './App.css';
import './components/LayerGrid.css';

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
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
    if (savedAudio) {
      setAudioDeviceId(savedAudio);
    }
    if (savedMidi) {
      setMidiDeviceId(savedMidi);
    }
  }, []);

  // Enumerar monitores disponibles
  useEffect(() => {
    const loadMonitors = async () => {
      if ((window as any).__TAURI__) {
        try {
          const mons = await availableMonitors();
          const mapped = mons.map((m, idx) => ({
            id: m.name || `monitor-${idx}`,
            label: m.name || `Monitor ${idx + 1}`,
            position: { x: m.position.x, y: m.position.y },
            size: { width: m.size.width, height: m.size.height }
          }));
          setMonitors(mapped);
          setSelectedMonitors(mapped.map(m => m.id));
        } catch (err) {
          console.warn('Monitor enumeration failed:', err);
          const fallback = {
            id: 'primary',
            label: 'Primary Monitor',
            position: { x: 0, y: 0 },
            size: { width: window.innerWidth, height: window.innerHeight }
          };
          setMonitors([fallback]);
          setSelectedMonitors([fallback.id]);
        }
      } else {
        const fallback = {
          id: 'primary',
          label: 'Primary Monitor',
          position: { x: 0, y: 0 },
          size: { width: window.innerWidth, height: window.innerHeight }
        };
        setMonitors([fallback]);
        setSelectedMonitors([fallback.id]);
      }
    };
    loadMonitors();
  }, []);

  // Persistir capas activas para modo fullscreen
  useEffect(() => {
    localStorage.setItem('activeLayers', JSON.stringify(activeLayers));
  }, [activeLayers]);

  // Cerrar ventana fullscreen con ESC o F11
  useEffect(() => {
    if (isFullscreenMode) {
      const handler = (e: KeyboardEvent) => {
        if (e.key === 'Escape' || e.key === 'F11') {
          window.close();
        }
      };
      window.addEventListener('keydown', handler);
      return () => window.removeEventListener('keydown', handler);
    }
  }, [isFullscreenMode]);

  const handleSelectAudio = (id: string) => {
    setAudioDeviceId(id || null);
    if (id) {
      localStorage.setItem('selectedAudioDevice', id);
    } else {
      localStorage.removeItem('selectedAudioDevice');
    }
  };

  const handleSelectMidi = (id: string) => {
    setMidiDeviceId(id || null);
    if (id) {
      localStorage.setItem('selectedMidiDevice', id);
    } else {
      localStorage.removeItem('selectedMidiDevice');
    }
  };

  const scaleAudio = (d: AudioData): AudioData => ({
    low: d.low * audioGain,
    mid: d.mid * audioGain,
    high: d.high * audioGain,
    fft: d.fft.map(v => v * audioGain)
  });

  // Inicializar el engine
  useEffect(() => {
    const initEngine = async () => {
      if (!canvasRef.current) {
        console.error('❌ Canvas ref is null');
        return;
      }

      console.log('🔧 Canvas found, initializing engine...');

      try {
        setStatus('Cargando presets...');

        const engine = new AudioVisualizerEngine(canvasRef.current, { glitchTextPads });
        await engine.initialize();

        engineRef.current = engine;

        const presets = engine.getAvailablePresets();
        setAvailablePresets(presets);
        setIsInitialized(true);
        setStatus('Listo');

        console.log(`✅ Engine initialized with ${presets.length} presets`);
      } catch (error) {
        console.error('❌ Failed to initialize engine:', error);
        setStatus('Error al inicializar');
      }
    };

    console.log('🚀 Starting app initialization...');
    initEngine();

    return () => {
      if (engineRef.current) {
        engineRef.current.dispose();
      }
    };
  }, []);

  // Enumerar dispositivos de audio
  useEffect(() => {
    if (navigator?.mediaDevices?.enumerateDevices) {
      navigator.mediaDevices.enumerateDevices()
        .then(devs => {
          const inputs = devs.filter(d => d.kind === 'audioinput');
          setAudioDevices(inputs);
          if (audioDeviceId && !inputs.some(d => d.deviceId === audioDeviceId)) {
            setAudioDeviceId(null);
          }
        })
        .catch(err => console.warn('Audio devices error', err));
    }
  }, [audioDeviceId]);

  // Configurar MIDI
  useEffect(() => {
    const handleMIDIMessage = (event: any) => {
      setMidiActive(true);
      setTimeout(() => setMidiActive(false), 100);

      const [statusByte] = event.data;
      if (statusByte === 0xf8) { // MIDI Clock
        const now = performance.now();
        const times = clockTimesRef.current;
        times.push(now);
        if (times.length > 24) times.shift();
        if (times.length >= 2) {
          const diff = (times[times.length - 1] - times[0]) / (times.length - 1);
          const bpmVal = 60000 / (diff * 24);
          setBpm(bpmVal);
        }
      }
    };

    if ((navigator as any).requestMIDIAccess) {
      (navigator as any).requestMIDIAccess()
        .then((access: any) => {
          const inputs = Array.from(access.inputs.values());
          setMidiDevices(inputs);
          inputs.forEach((input: any) => {
            if (!midiDeviceId || input.id === midiDeviceId) {
              input.onmidimessage = handleMIDIMessage;
            } else {
              input.onmidimessage = null;
            }
          });
          access.onstatechange = () => {
            const ins = Array.from(access.inputs.values());
            setMidiDevices(ins);
          };
        })
        .catch((err: any) => console.warn('MIDI access error', err));
    }
  }, [midiDeviceId]);

  // Configurar listener de audio - VERSIÓN MEJORADA
  useEffect(() => {
    let teardown: (() => void) | undefined;
    const setupAudioListener = async () => {
      try {
        // Detectar si estamos en un entorno Tauri
        if (typeof window !== 'undefined' && (window as any).__TAURI__) {
          console.log('🎵 Tauri environment detected, setting up audio listener...');
          
          // Importación dinámica solo en entorno Tauri
          const tauriApi = await import('@tauri-apps/api/event');
          
          const unlisten = await tauriApi.listen('audio_data', (event) => {
            const data = event.payload as AudioData;
            const scaled = scaleAudio(data);
            setAudioData(scaled);

            if (engineRef.current) {
              engineRef.current.updateAudioData(scaled);
            }
          });
          
          console.log('✅ Tauri audio listener setup complete');
          teardown = () => { unlisten(); };
        } else {
          console.log('🎙️ Using Web Audio API for input');

          const constraints: MediaStreamConstraints = {
            audio: audioDeviceId ? { deviceId: { exact: audioDeviceId } } : true
          };
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          const AudioContextClass =
            (window as any).AudioContext || (window as any).webkitAudioContext;
          const audioCtx = new AudioContextClass();
          const source = audioCtx.createMediaStreamSource(stream);
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 512;
          source.connect(analyser);
          const bufferLength = analyser.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);

          let rafId = 0;
          const update = () => {
            analyser.getByteFrequencyData(dataArray);
            const third = Math.floor(bufferLength / 3);
            const avg = (arr: Uint8Array) =>
              arr.reduce((sum, v) => sum + v, 0) / arr.length / 255;
            const low = avg(dataArray.slice(0, third));
            const mid = avg(dataArray.slice(third, third * 2));
            const high = avg(dataArray.slice(third * 2));
            const fft = Array.from(dataArray, v => v / 255);
            const scaled = scaleAudio({ low, mid, high, fft });
            setAudioData(scaled);
            if (engineRef.current) {
              engineRef.current.updateAudioData(scaled);
            }
            rafId = requestAnimationFrame(update);
          };
          rafId = requestAnimationFrame(update);

          teardown = () => {
            cancelAnimationFrame(rafId);
            audioCtx.close();
            stream.getTracks().forEach(t => t.stop());
          };
        }
      } catch (error) {
        console.warn('⚠️ Audio listener setup failed:', error);
        
        // Fallback: datos de audio estáticos
        const fallbackData: AudioData = {
          low: 0.3,
          mid: 0.5,
          high: 0.2,
          fft: Array.from({ length: 256 }, () => Math.random() * 0.5)
        };
        
        const scaled = scaleAudio(fallbackData);
        setAudioData(scaled);

        if (engineRef.current) {
          engineRef.current.updateAudioData(scaled);
        }
      }
    };

    if (isInitialized) {
      setupAudioListener();
    }
    return () => {
      if (teardown) teardown();
    };
  }, [isInitialized, audioGain, audioDeviceId]);

  // Activar capas almacenadas en modo fullscreen
  useEffect(() => {
    if (isFullscreenMode && isInitialized && engineRef.current) {
      const stored = localStorage.getItem('activeLayers');
      if (stored) {
        const layers = JSON.parse(stored) as Record<string, string>;
        Object.entries(layers).forEach(([layerId, presetId]) => {
          engineRef.current!.activatePreset(layerId, presetId);
        });
      }
    }
  }, [isFullscreenMode, isInitialized]);

  // Monitor FPS
  useEffect(() => {
    let frameCount = 0;
    let lastTime = Date.now();

    const updateFPS = () => {
      frameCount++;
      const currentTime = Date.now();
      
      if (currentTime - lastTime >= 1000) {
        setFps(frameCount);
        frameCount = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(updateFPS);
    };

    if (isInitialized) {
      updateFPS();
    }
  }, [isInitialized]);

  // Handlers para LayerGrid
  const handlePresetActivate = (layerId: string, presetId: string) => {
    if (!engineRef.current) return;

    console.log(`🎨 Activating preset ${presetId} on layer ${layerId}`);

    const success = engineRef.current.activatePreset(layerId, presetId);
    if (success) {
      setActiveLayers(prev => ({ ...prev, [layerId]: presetId }));
      setStatus(`Layer ${layerId}: ${availablePresets.find(p => p.id === presetId)?.config.name}`);
      setSelectedPreset(availablePresets.find(p => p.id === presetId) || null);
      setSelectedLayer(layerId);
    }
  };

  const handleLayerClear = (layerId: string) => {
    if (!engineRef.current) return;

    console.log(`🗑️ Clearing layer ${layerId}`);
    engineRef.current.deactivateLayerPreset(layerId);
    
    setActiveLayers(prev => {
      const newLayers = { ...prev };
      delete newLayers[layerId];
      return newLayers;
    });
    
    setStatus(`Layer ${layerId} cleared`);
  };

  const handleLayerConfigChange = (layerId: string, config: any) => {
    if (!engineRef.current) return;

    console.log(`⚙️ Layer ${layerId} config changed:`, config);
    
    // Aplicar cambios de opacidad
    if (config.opacity !== undefined) {
      engineRef.current.setLayerOpacity(layerId, config.opacity / 100);
    }

    // Aplicar otros cambios de configuración
    engineRef.current.updateLayerConfig(layerId, config);
  };

  const handlePresetConfigUpdate = (config: any) => {
    if (!engineRef.current || !selectedLayer) return;
    engineRef.current.updateLayerConfig(selectedLayer, config);
  };

  const getCurrentPresetName = (): string => {
    const activeLayerIds = Object.keys(activeLayers);
    if (activeLayerIds.length === 0) return 'Ninguno';
    
    const activePresets = activeLayerIds.map(layerId => {
      const presetId = activeLayers[layerId];
      const preset = availablePresets.find(p => p.id === presetId);
      return `${layerId}: ${preset?.config.name || presetId}`;
    });
    
    return activePresets.join(', ');
  };

  const midiDeviceName = midiDeviceId ? midiDevices.find((d: any) => d.id === midiDeviceId)?.name || null : null;
  const audioDeviceName = audioDeviceId ? audioDevices.find(d => d.deviceId === audioDeviceId)?.label || null : null;
  const audioLevel = Math.min((audioData.low + audioData.mid + audioData.high) / 3, 1);

  const handleAudioGainChange = (value: number) => setAudioGain(value);
  const handleFullScreen = () => {
    if ((window as any).__TAURI__) {
      localStorage.setItem('activeLayers', JSON.stringify(activeLayers));
      monitors
        .filter(m => selectedMonitors.includes(m.id))
        .forEach(m => {
          const label = `fullscreen-${m.id}-${Date.now()}`;
          new WebviewWindow(label, {
            url: 'index.html?fullscreen=true',
            x: m.position.x,
            y: m.position.y,
            width: m.size.width,
            height: m.size.height,
            decorations: false,
            fullscreen: true,
            skipTaskbar: true
          });
        });
    } else {
      const elem: any = document.documentElement;
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
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
    setSelectedMonitors(prev => prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]);
  };

  const handleGlitchPadCountChange = async (value: number) => {
    setGlitchTextPads(value);
    localStorage.setItem('glitchTextPads', value.toString());
    if (engineRef.current) {
      const presets = await engineRef.current.updateGlitchPadCount(value);
      setAvailablePresets(presets);
    }
  };

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
        onAudioGainChange={handleAudioGainChange}
        audioLevel={audioLevel}
        onFullScreen={handleFullScreen}
        onClearAll={handleClearAll}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Grid de capas */}
      <div className="layer-grid-container">
        <LayerGrid
          presets={availablePresets}
          onPresetActivate={handlePresetActivate}
          onLayerClear={handleLayerClear}
          onLayerConfigChange={handleLayerConfigChange}
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
              onConfigUpdate={handlePresetConfigUpdate}
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
        onSelectAudio={handleSelectAudio}
        onSelectMidi={handleSelectMidi}
        audioGain={audioGain}
        onAudioGainChange={handleAudioGainChange}
        monitors={monitors}
        selectedMonitors={selectedMonitors}
        onToggleMonitor={handleToggleMonitor}
        glitchTextPads={glitchTextPads}
        onGlitchPadChange={handleGlitchPadCountChange}
      />
    </div>
  );
};

export default App;