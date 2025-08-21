// App.tsx - Corregido y completo con todas las mejoras

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { AudioVisualizerEngine } from './core/AudioVisualizerEngine';
import { LayerGrid } from './components/LayerGrid';
import { StatusBar } from './components/StatusBar';
import { PresetControls } from './components/PresetControls';
import { TopBar } from './components/TopBar';
import { GlobalSettingsModal } from './components/GlobalSettingsModal';
import { LoadedPreset, AudioData } from './core/PresetLoader';
import { setNestedValue } from './utils/objectPath';
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
  const tickCountRef = useRef(0);
  const lastBeatRef = useRef<number | null>(null);
  const bpmSamplesRef = useRef<number[]>([]);
  const broadcastRef = useRef<BroadcastChannel | null>(null);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [availablePresets, setAvailablePresets] = useState<LoadedPreset[]>([]);
  const [audioData, setAudioData] = useState<AudioData>({ low: 0, mid: 0, high: 0, fft: [] });
  const [fps, setFps] = useState(60);
  const [status, setStatus] = useState('Inicializando...');
  const [activeLayers, setActiveLayers] = useState<Record<string, string>>({});
  const [selectedPreset, setSelectedPreset] = useState<LoadedPreset | null>(null);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
  const [isControlsOpen, setIsControlsOpen] = useState(() => {
    const stored = localStorage.getItem('sidebarCollapsed');
    if (stored === null) return false;
    return stored !== 'true';
  });
  const [layerPresetConfigs, setLayerPresetConfigs] = useState<Record<string, Record<string, any>>>(() => {
    try {
      const stored = localStorage.getItem('layerPresetConfigs');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  // Top bar & settings state
  const [midiDevices, setMidiDevices] = useState<any[]>([]);
  const [midiDeviceId, setMidiDeviceId] = useState<string | null>(null);
  const [midiActive, setMidiActive] = useState(false);
  const [bpm, setBpm] = useState<number | null>(null);
  const [beatActive, setBeatActive] = useState(false);
  const [midiTrigger, setMidiTrigger] = useState<{layerId: string; presetId: string} | null>(null);
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [audioDeviceId, setAudioDeviceId] = useState<string | null>(null);
  const [audioGain, setAudioGain] = useState(1);
  const [midiClockDelay, setMidiClockDelay] = useState(() => parseInt(localStorage.getItem('midiClockDelay') || '0'));
  const [midiClockType, setMidiClockType] = useState(() => localStorage.getItem('midiClockType') || 'midi');
  const [layerChannels, setLayerChannels] = useState<Record<string, number>>(() => {
    const saved = localStorage.getItem('layerMidiChannels');
    return saved ? JSON.parse(saved) : { A: 14, B: 15, C: 16 };
  });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [monitors, setMonitors] = useState<MonitorInfo[]>([]);
  const [selectedMonitors, setSelectedMonitors] = useState<string[]>([]);
  const [glitchTextPads, setGlitchTextPads] = useState<number>(() => parseInt(localStorage.getItem('glitchTextPads') || '1'));
  const [clearSignal, setClearSignal] = useState(0);
  const [isFullscreenMode, setIsFullscreenMode] = useState(
    () => new URLSearchParams(window.location.search).get('fullscreen') === 'true'
  );
  const [hideUiHotkey, setHideUiHotkey] = useState(() => localStorage.getItem('hideUiHotkey') || 'F10');
  const [isUiHidden, setIsUiHidden] = useState(false);
  const [startMaximized, setStartMaximized] = useState(() => localStorage.getItem('startMaximized') !== 'false');
  const [startMonitor, setStartMonitor] = useState<string | null>(() => localStorage.getItem('startMonitor'));

  useEffect(() => {
    const channel = new BroadcastChannel('av-sync');
    broadcastRef.current = channel;
    return () => channel.close();
  }, []);

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

  useEffect(() => {
    localStorage.setItem('startMaximized', startMaximized.toString());
  }, [startMaximized]);

  useEffect(() => {
    if (startMonitor) {
      localStorage.setItem('startMonitor', startMonitor);
    } else {
      localStorage.removeItem('startMonitor');
    }
  }, [startMonitor]);

  useEffect(() => {
    (window as any).electronAPI?.applySettings({
      maximize: startMaximized,
      monitorId: startMonitor ? parseInt(startMonitor, 10) : undefined
    });
  }, [startMaximized, startMonitor]);

  // Persist preset configs per layer/visual automatically
  useEffect(() => {
    try {
      localStorage.setItem('layerPresetConfigs', JSON.stringify(layerPresetConfigs));
      broadcastRef.current?.postMessage({ type: 'layerPresetConfigs', data: layerPresetConfigs });
    } catch (e) {
      console.warn('Failed to persist layer preset configs:', e);
    }
  }, [layerPresetConfigs]);


  // Enumerar monitores disponibles usando Electron
  useEffect(() => {
    const loadMonitors = async () => {
      if ((window as any).electronAPI?.getDisplays) {
        try {
          const displays = await (window as any).electronAPI.getDisplays();
          const mapped: MonitorInfo[] = displays.map((d: any) => ({
            id: d.id.toString(),
            label: `${d.label} (${d.bounds.width}x${d.bounds.height})`,
            position: { x: d.bounds.x, y: d.bounds.y },
            size: { width: d.bounds.width, height: d.bounds.height },
            isPrimary: d.primary,
            scaleFactor: d.scaleFactor || 1
          }));
          mapped.sort((a, b) => {
            if (a.isPrimary !== b.isPrimary) return a.isPrimary ? -1 : 1;
            return a.position.x - b.position.x;
          });
          setMonitors(mapped);
          if (selectedMonitors.length === 0 && mapped.length > 0) {
            const primary = mapped.find(m => m.isPrimary) || mapped[0];
            setSelectedMonitors([primary.id]);
          }
        } catch (e) {
          console.warn('Error loading monitors:', e);
        }
      }
    };
    loadMonitors();
  }, []);

  useEffect(() => {
    const handler = () => {
      const param = new URLSearchParams(window.location.search).get('fullscreen') === 'true';
      setIsFullscreenMode(param || !!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

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
  }, [glitchTextPads]);

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
      const [statusByte, note, vel] = event.data;

      // MIDI Start/Stop/Continue handling
      if (statusByte === 0xfa || statusByte === 0xfb || statusByte === 0xfc) {
        tickCountRef.current = 0;
        lastBeatRef.current = null;
        bpmSamplesRef.current = [];
        if (statusByte === 0xfc) {
          setBpm(null);
        }
        return;
      }

      // MIDI Clock handling
      if (statusByte === 0xf8 && midiClockType === 'midi') {
        const now = performance.now();
        tickCountRef.current++;

        if (tickCountRef.current >= 24) {
          const lastBeat = lastBeatRef.current;
          if (lastBeat !== null) {
            const diff = now - lastBeat;
            const bpmVal = 60000 / diff;
            if (isFinite(bpmVal)) {
              bpmSamplesRef.current.push(bpmVal);
              if (bpmSamplesRef.current.length > 8) bpmSamplesRef.current.shift();
              const avg = bpmSamplesRef.current.reduce((a, b) => a + b, 0) / bpmSamplesRef.current.length;
              setBpm(avg);
              if (engineRef.current) {
                engineRef.current.updateBpm(avg);
              }
            }
          }
          lastBeatRef.current = now;
          tickCountRef.current = 0;

          const trigger = () => {
            setBeatActive(true);
            setTimeout(() => setBeatActive(false), 100);
            if (engineRef.current) {
              engineRef.current.triggerBeat();
            }
          };

          if (midiClockDelay > 0) {
            setTimeout(trigger, midiClockDelay);
          } else {
            trigger();
          }
        }
        return;
      }

      // Note on messages
      const command = statusByte & 0xf0;
      const channel = (statusByte & 0x0f) + 1;
      if (command === 0x90 && vel > 0) {
        const channelToLayer = Object.fromEntries(
          Object.entries(layerChannels).map(([layerId, ch]) => [ch, layerId])
        ) as Record<number, string>;
        const layerId = channelToLayer[channel];
        const preset = availablePresets.find(p => p.config.note === note);
        if (layerId && preset) {
          setMidiTrigger({ layerId, presetId: preset.id });
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
  }, [midiDeviceId, midiClockType, midiClockDelay, layerChannels, availablePresets]);

  // Configurar listener de audio
  useEffect(() => {
    let teardown: (() => void) | undefined;

    const scaleAudio = (d: AudioData): AudioData => ({
      low: d.low * audioGain,
      mid: d.mid * audioGain,
      high: d.high * audioGain,
      fft: d.fft.map(v => v * audioGain)
    });

    const setupAudioListener = async () => {
      try {
        if (typeof window !== 'undefined' && (window as any).__TAURI__) {
          console.log('🎵 Tauri environment detected, setting up audio listener...');
          
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
          const AudioContextClass = (window as any).AudioContext || (window as any).webkitAudioContext;
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
            
            const avg = (arr: Uint8Array) => arr.reduce((sum, v) => sum + v, 0) / arr.length / 255;
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
          engineRef.current!.activateLayerPreset(layerId, presetId);
        });
      }
    }
  }, [isFullscreenMode, isInitialized]);

  // Cerrar ventana fullscreen con ESC o F11
  useEffect(() => {
    if (isFullscreenMode) {
      const handler = (e: KeyboardEvent) => {
        if (e.key === 'Escape' || e.key === 'F11') {
          if ((window as any).__TAURI__) {
            window.close();
          } else if (document.fullscreenElement) {
            document.exitFullscreen();
          }
        }
      };
      window.addEventListener('keydown', handler);
      return () => window.removeEventListener('keydown', handler);
    }
  }, [isFullscreenMode]);

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

  // Persistir capas activas para modo fullscreen
  useEffect(() => {
    localStorage.setItem('activeLayers', JSON.stringify(activeLayers));
    broadcastRef.current?.postMessage({ type: 'activeLayers', data: activeLayers });
  }, [activeLayers]);

  // Toggle UI visibility with configurable hotkey
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key.toUpperCase() === hideUiHotkey.toUpperCase()) {
        e.preventDefault();
        setIsUiHidden(prev => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [hideUiHotkey]);

  // Handlers
  const handleFullScreen = useCallback(async () => {
    if ((window as any).electronAPI) {
      localStorage.setItem('activeLayers', JSON.stringify(activeLayers));
      const ids = selectedMonitors.map(id => parseInt(id, 10)).filter(Boolean);
      if (ids.length === 0) {
        setStatus('Error: No hay monitores seleccionados');
        return;
      }
      try {
        await (window as any).electronAPI.toggleFullscreen(ids);
        setStatus(`Fullscreen toggled en ${ids.length} monitor(es)`);
      } catch (err) {
        console.error('Error en fullscreen:', err);
        setStatus('Error: No se pudo activar fullscreen');
      }
    } else if ((window as any).__TAURI__) {
      localStorage.setItem('activeLayers', JSON.stringify(activeLayers));

      try {
        const { WebviewWindow } = await import(
          /* @vite-ignore */ '@tauri-apps/api/window'
        );

        const selectedMonitorsList = monitors.filter(m => selectedMonitors.includes(m.id));

        if (selectedMonitorsList.length === 0) {
          setStatus('Error: No hay monitores seleccionados');
          return;
        }

        console.log(`🎯 Abriendo fullscreen en ${selectedMonitorsList.length} monitores`);

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
      const elem: any = document.documentElement;
      if (elem.requestFullscreen) {
        await elem.requestFullscreen();
        setIsFullscreenMode(true);
        setStatus('Fullscreen activado (navegador)');
      } else {
        setStatus('Error: Fullscreen no disponible');
      }
    }
  }, [activeLayers, selectedMonitors, monitors]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'F9') {
        e.preventDefault();
        handleFullScreen();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleFullScreen]);

  const handleClearAll = () => {
    if (!engineRef.current) return;
    ['A', 'B', 'C'].forEach(layerId => engineRef.current?.deactivateLayerPreset(layerId));
    engineRef.current.clearRenderer();
    setActiveLayers({});
    setSelectedPreset(null);
    setSelectedLayer(null);
    setClearSignal(prev => prev + 1);
    setStatus('Capas limpiadas');
  };

  const applyPresetConfig = (
    engine: AudioVisualizerEngine,
    layerId: string,
    cfg: Record<string, any>,
    prefix = ''
  ) => {
    Object.entries(cfg).forEach(([key, value]) => {
      const path = prefix ? `${prefix}.${key}` : key;
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        applyPresetConfig(engine, layerId, value as Record<string, any>, path);
      } else {
        engine.updateLayerPresetConfig(layerId, path, value);
      }
    });
  };

  useEffect(() => {
    if (!isFullscreenMode) return;
    const channel = broadcastRef.current;
    if (!channel) return;

    const handler = (event: MessageEvent) => {
      const msg = event.data;
      if (!engineRef.current) return;
      switch (msg.type) {
        case 'activeLayers': {
          const newActive = msg.data as Record<string, string>;
          Object.keys(activeLayers).forEach(layerId => {
            if (!newActive[layerId]) {
              engineRef.current!.deactivateLayerPreset(layerId);
            }
          });
          Object.entries(newActive).forEach(([layerId, presetId]) => {
            engineRef.current!.activateLayerPreset(layerId, presetId);
            const cfg = layerPresetConfigs[layerId]?.[presetId];
            if (cfg) applyPresetConfig(engineRef.current!, layerId, cfg);
          });
          setActiveLayers(newActive);
          break;
        }
        case 'layerConfig': {
          engineRef.current.updateLayerConfig(msg.layerId, msg.config);
          break;
        }
        case 'layerPresetConfigs': {
          const cfgs = msg.data as Record<string, Record<string, any>>;
          setLayerPresetConfigs(cfgs);
          Object.entries(activeLayers).forEach(([layerId, presetId]) => {
            const cfg = cfgs[layerId]?.[presetId];
            if (cfg) applyPresetConfig(engineRef.current!, layerId, cfg);
          });
          break;
        }
      }
    };

    channel.addEventListener('message', handler);
    return () => channel.removeEventListener('message', handler);
  }, [isFullscreenMode, activeLayers, layerPresetConfigs]);

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

  const getCurrentPresetName = (): string => {
    if (!selectedPreset) return 'Ninguno';
    return `${selectedPreset.config.name} (${selectedLayer || 'N/A'})`;
  };

  const midiDeviceName = midiDeviceId ? midiDevices.find((d: any) => d.id === midiDeviceId)?.name || null : null;
  const audioDeviceName = audioDeviceId ? audioDevices.find(d => d.deviceId === audioDeviceId)?.label || null : null;
  const audioLevel = Math.min((audioData.low + audioData.mid + audioData.high) / 3, 1);

  return (
    <div className={`app ${isUiHidden ? 'ui-hidden' : ''}`}>
      <TopBar
        midiActive={midiActive}
        midiDeviceName={midiDeviceName}
        midiDeviceCount={midiDevices.length}
        bpm={bpm}
        beatActive={beatActive}
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
          externalTrigger={midiTrigger}
          onPresetActivate={async (layerId, presetId) => {
            if (engineRef.current) {
              await engineRef.current.activateLayerPreset(layerId, presetId);
              setActiveLayers(prev => ({ ...prev, [layerId]: presetId }));

              const preset = availablePresets.find(p => p.id === presetId);
              if (preset) {
                const existing = layerPresetConfigs[layerId]?.[presetId];
                if (existing) {
                  applyPresetConfig(engineRef.current, layerId, existing);
                } else {
                  const cfg = engineRef.current.getLayerPresetConfig(layerId, presetId);
                  setLayerPresetConfigs(prev => ({
                    ...prev,
                    [layerId]: { ...(prev[layerId] || {}), [presetId]: cfg }
                  }));
                }
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
            broadcastRef.current?.postMessage({ type: 'layerConfig', layerId, config });
          }}
          onPresetSelect={(layerId, presetId) => {
            if (presetId) {
              const preset = availablePresets.find(p => p.id === presetId);
              if (preset) {
                const existing = layerPresetConfigs[layerId]?.[presetId];
                if (!existing) {
                  const cfg = engineRef.current?.getLayerPresetConfig(layerId, presetId);
                  if (cfg) {
                    setLayerPresetConfigs(prev => ({
                      ...prev,
                      [layerId]: { ...(prev[layerId] || {}), [presetId]: cfg }
                    }));
                  }
                }
                setSelectedPreset(preset);
                setSelectedLayer(layerId);
              }
            } else if (selectedLayer === layerId) {
              setSelectedPreset(null);
              setSelectedLayer(null);
            }
          }}
          clearAllSignal={clearSignal}
          layerChannels={layerChannels}
        />
      </div>

      {/* Sección inferior con visuales y controles */}
      <div className="bottom-section">
        <canvas ref={canvasRef} className="main-canvas" />
        <div className={`controls-panel ${isControlsOpen ? '' : 'collapsed'}`}>
          <button
            className="toggle-sidebar"
            onClick={() =>
              setIsControlsOpen(prev => {
                const next = !prev;
                localStorage.setItem('sidebarCollapsed', (!next).toString());
                return next;
              })
            }
          >
            {isControlsOpen ? '✕' : '⚙️'}
          </button>
          {isControlsOpen && selectedPreset && (
            <PresetControls
              preset={selectedPreset}
              config={layerPresetConfigs[selectedLayer!]?.[selectedPreset.id]}
              onConfigUpdate={(path, value) => {
                if (engineRef.current && selectedLayer && selectedPreset) {
                  engineRef.current.updateLayerPresetConfig(selectedLayer, path, value);
                  setLayerPresetConfigs(prev => {
                    const layerMap = { ...(prev[selectedLayer] || {}) };
                    const cfg = { ...(layerMap[selectedPreset.id] || {}) };
                    setNestedValue(cfg, path, value);
                    layerMap[selectedPreset.id] = cfg;
                    return { ...prev, [selectedLayer]: layerMap };
                  });
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
        midiClockDelay={midiClockDelay}
        onMidiClockDelayChange={(v) => {
          setMidiClockDelay(v);
          localStorage.setItem('midiClockDelay', v.toString());
        }}
        midiClockType={midiClockType}
        onMidiClockTypeChange={(t) => {
          setMidiClockType(t);
          localStorage.setItem('midiClockType', t);
        }}
        layerChannels={layerChannels}
        onLayerChannelChange={(layerId, channel) => {
          const updated = { ...layerChannels, [layerId]: channel };
          setLayerChannels(updated);
          localStorage.setItem('layerMidiChannels', JSON.stringify(updated));
        }}
        monitors={monitors}
        selectedMonitors={selectedMonitors}
        onToggleMonitor={handleToggleMonitor}
        startMonitor={startMonitor}
        onStartMonitorChange={setStartMonitor}
        glitchTextPads={glitchTextPads}
        onGlitchPadChange={async (value: number) => {
          setGlitchTextPads(value);
          localStorage.setItem('glitchTextPads', value.toString());
          if (engineRef.current) {
            const presets = await engineRef.current.updateGlitchPadCount(value);
            setAvailablePresets(presets);
          }
        }}
        startMaximized={startMaximized}
        onStartMaximizedChange={setStartMaximized}
        sidebarCollapsed={!isControlsOpen}
        onSidebarCollapsedChange={(value) => {
          localStorage.setItem('sidebarCollapsed', value.toString());
          setIsControlsOpen(!value);
        }}
        hideUiHotkey={hideUiHotkey}
        onHideUiHotkeyChange={(key) => {
          setHideUiHotkey(key);
          localStorage.setItem('hideUiHotkey', key);
        }}
      />
    </div>
  );
};

export default App;