// App.tsx - Completo con todas las mejoras del presets gallery

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { AudioVisualizerEngine } from './core/AudioVisualizerEngine';
import { AppSelector, AppMode } from './components/AppSelector';
import { CreaLab } from './crealab/components/CreaLab';
import { LayerGrid } from './components/LayerGrid';
import { StatusBar } from './components/StatusBar';
import { PresetControls } from './components/PresetControls';
import { TopBar } from './components/TopBar';
import { ResourcesModal } from './components/ResourcesModal';
import { GlobalSettingsModal } from './components/GlobalSettingsModal';
import { LoadedPreset } from './core/PresetLoader';
import { setNestedValue } from './utils/objectPath';
import { AVAILABLE_EFFECTS } from './utils/effects';
import { gridIndexToNote, LAUNCHPAD_PRESETS } from './utils/launchpad';
import { useAudio } from './hooks/useAudio';
import { useMidi } from './hooks/useMidi';
import { useLaunchpad } from './hooks/useLaunchpad';
import './App.css';
import './AppLayout.css';
import './AppRouter.css';

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
  const broadcastRef = useRef<BroadcastChannel | null>(null);
  // App routing state
  const [currentApp, setCurrentApp] = useState<AppMode | null>(null);

  const [isInitialized, setIsInitialized] = useState(false);
  const [availablePresets, setAvailablePresets] = useState<LoadedPreset[]>([]);
  const [fps, setFps] = useState(60);
  const [status, setStatus] = useState('Initializing...');
  const [activeLayers, setActiveLayers] = useState<Record<string, string>>({});
  const [selectedPreset, setSelectedPreset] = useState<LoadedPreset | null>(null);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
  // Check if user has a preference for app selection
  useEffect(() => {
    const savedApp = localStorage.getItem('jungle-lab-preferred-app') as AppMode;
    if (savedApp && ['audiovisualizer', 'crealab'].includes(savedApp)) {
      setCurrentApp(savedApp);
    }
    }, []);
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

  const [genLabPresets, setGenLabPresets] = useState<{ name: string; config: any }[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('genLabPresets') || '[]');
    } catch {
      return [];
    }
  });
  const [genLabBasePreset, setGenLabBasePreset] = useState<LoadedPreset | null>(null);
  const [fractalLabPresets, setFractalLabPresets] = useState<{ name: string; config: any }[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('fractalLabPresets') || '[]');
    } catch {
      return [];
    }
  });
  const [fractalLabBasePreset, setFractalLabBasePreset] = useState<LoadedPreset | null>(null);

  // Top bar & settings state
  const [layerChannels, setLayerChannels] = useState<Record<string, number>>(() => {
    const saved = localStorage.getItem('layerMidiChannels');
    return saved ? JSON.parse(saved) : { A: 14, B: 15, C: 16 };
  });
  const [effectMidiNotes, setEffectMidiNotes] = useState<Record<string, number>>(() => {
    try {
      const stored = localStorage.getItem('effectMidiNotes');
      if (stored) return JSON.parse(stored);
    } catch {}
    const defaults: Record<string, number> = {};
    AVAILABLE_EFFECTS.forEach((eff, idx) => {
      if (eff !== 'none') defaults[eff] = 80 + idx;
    });
    return defaults;
  });
  const [layerEffects, setLayerEffects] = useState<Record<string, { effect: string; alwaysOn: boolean; active: boolean }>>(() => {
    try {
      const stored = localStorage.getItem('layerEffects');
      if (stored) {
        const parsed = JSON.parse(stored);
        const ensure = (layer: any) => ({
          effect: layer?.effect || 'none',
          alwaysOn: layer?.alwaysOn || false,
          active: layer?.alwaysOn || false,
        });
        return {
          A: ensure(parsed.A),
          B: ensure(parsed.B),
          C: ensure(parsed.C),
        };
      }
    } catch {}
    return {
      A: { effect: 'none', alwaysOn: false, active: false },
      B: { effect: 'none', alwaysOn: false, active: false },
      C: { effect: 'none', alwaysOn: false, active: false },
    };
  });

  const [isFullscreenMode, setIsFullscreenMode] = useState(
    () => new URLSearchParams(window.location.search).get('fullscreen') === 'true'
  );

  const {
    audioData,
    audioDevices,
    audioDeviceId,
    setAudioDeviceId,
    audioGain,
    setAudioGain,
  } = useAudio(engineRef, isInitialized);

  const {
    launchpadOutputs,
    launchpadId,
    setLaunchpadId,
    launchpadOutput,
    launchpadRunning,
    setLaunchpadRunning,
    launchpadPreset,
    setLaunchpadPreset,
    launchpadChannel,
    setLaunchpadChannel,
    launchpadNote,
    setLaunchpadNote,
    launchpadSmoothness,
    setLaunchpadSmoothness,
    launchpadText,
    setLaunchpadText,
  } = useLaunchpad(audioData, canvasRef);

  const {
    midiDevices,
    midiDeviceId,
    setMidiDeviceId,
    midiActive,
    bpm,
    beatActive,
    midiTrigger,
    setMidiTrigger,
    midiClockSettings,
    updateClockSettings,
    setInternalBpm,
    internalBpm,
    clockStable,
    currentMeasure,
    currentBeat,
  } = useMidi({
    isFullscreenMode,
    availablePresets,
    layerChannels,
    layerEffects,
    setLayerEffects,
    effectMidiNotes,
    launchpadChannel,
    launchpadNote,
    onLaunchpadToggle: () => setLaunchpadRunning(prev => !prev),
    engineRef,
  });
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isResourcesOpen, setResourcesOpen] = useState(false);
  const [monitors, setMonitors] = useState<MonitorInfo[]>([]);
  const [monitorRoles, setMonitorRoles] = useState<Record<string, 'main' | 'secondary' | 'none'>>(() => {
    try {
      return JSON.parse(localStorage.getItem('monitorRoles') || '{}');
    } catch {
      return {} as Record<string, 'main' | 'secondary' | 'none'>;
    }
  });
  const storedTemplate = (() => {
    try {
      return JSON.parse(localStorage.getItem('customTextTemplate') || '{}');
    } catch {
      return {};
    }
  })();
  const [glitchTextPads, setGlitchTextPads] = useState<number>(storedTemplate.count || parseInt(localStorage.getItem('glitchTextPads') || '1'));
  const [customTextContents, setCustomTextContents] = useState<string[]>(storedTemplate.texts || []);
  const [clearSignal, setClearSignal] = useState(0);
  const [hideUiHotkey, setHideUiHotkey] = useState(() => localStorage.getItem('hideUiHotkey') || 'F10');
  const [isUiHidden, setIsUiHidden] = useState(false);
  const [fullscreenHotkey, setFullscreenHotkey] = useState(() => localStorage.getItem('fullscreenHotkey') || 'F9');
  const [exitFullscreenHotkey, setExitFullscreenHotkey] = useState(() => localStorage.getItem('exitFullscreenHotkey') || 'F11');
  const [fullscreenByDefault, setFullscreenByDefault] = useState(() => localStorage.getItem('fullscreenByDefault') !== 'false');
  const [startMaximized, setStartMaximized] = useState(() => localStorage.getItem('startMaximized') !== 'false');
  const [startMonitor, setStartMonitor] = useState<string | null>(() => localStorage.getItem('startMonitor'));
  const [canvasBrightness, setCanvasBrightness] = useState(() => parseFloat(localStorage.getItem('canvasBrightness') || '1'));
  const [canvasVibrance, setCanvasVibrance] = useState(() => parseFloat(localStorage.getItem('canvasVibrance') || '1'));
  const [canvasBackground, setCanvasBackground] = useState(() => localStorage.getItem('canvasBackground') || '#000000');
  const [visualsPath, setVisualsPath] = useState(
    () => localStorage.getItem('visualsPath') || './src/presets/'
  );

  useEffect(() => {
    const channel = new BroadcastChannel('av-sync');
    broadcastRef.current = channel;
    return () => channel.close();
  }, []);

  // Persist selected devices across sessions
  useEffect(() => {
    const savedAudio = localStorage.getItem('selectedAudioDevice');
    const savedMidi = localStorage.getItem('selectedMidiDevice');
    const savedMonitorRoles = localStorage.getItem('monitorRoles');
    
    if (savedAudio) setAudioDeviceId(savedAudio);
    if (savedMidi) setMidiDeviceId(savedMidi);
    if (savedMonitorRoles) {
      try {
        setMonitorRoles(JSON.parse(savedMonitorRoles));
      } catch (e) {
        console.warn('Error parsing saved monitor roles:', e);
      }
    }
  }, []);

  // Persist monitor roles
  useEffect(() => {
    localStorage.setItem('monitorRoles', JSON.stringify(monitorRoles));
  }, [monitorRoles]);

  useEffect(() => {
    localStorage.setItem('startMaximized', startMaximized.toString());
  }, [startMaximized]);

  useEffect(() => {
    localStorage.setItem('fullscreenHotkey', fullscreenHotkey);
  }, [fullscreenHotkey]);

  useEffect(() => {
    localStorage.setItem('exitFullscreenHotkey', exitFullscreenHotkey);
  }, [exitFullscreenHotkey]);

  useEffect(() => {
    localStorage.setItem('fullscreenByDefault', fullscreenByDefault.toString());
  }, [fullscreenByDefault]);

  useEffect(() => {
    localStorage.setItem('canvasBrightness', canvasBrightness.toString());
  }, [canvasBrightness]);

  useEffect(() => {
    localStorage.setItem('canvasVibrance', canvasVibrance.toString());
  }, [canvasVibrance]);

  useEffect(() => {
    localStorage.setItem('canvasBackground', canvasBackground);
  }, [canvasBackground]);

  useEffect(() => {
    localStorage.setItem('visualsPath', visualsPath);
  }, [visualsPath]);

  useEffect(() => {
    if (!isFullscreenMode && midiTrigger) {
      broadcastRef.current?.postMessage({ type: 'midiTrigger', data: midiTrigger });
    }
  }, [midiTrigger, isFullscreenMode]);

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

  useEffect(() => {
    try {
      localStorage.setItem('layerEffects', JSON.stringify(layerEffects));
    } catch (e) {
      console.warn('Failed to persist layer effects:', e);
    }
  }, [layerEffects]);

  const activeEffectClasses = Object.entries(layerEffects)
    .filter(([, cfg]) => cfg.active && cfg.effect !== 'none')
    .map(([, cfg]) => `effect-${cfg.effect}`)
    .join(' ');

  useEffect(() => {
    try {
      localStorage.setItem('effectMidiNotes', JSON.stringify(effectMidiNotes));
    } catch (e) {
      console.warn('Failed to persist effect MIDI notes:', e);
    }
  }, [effectMidiNotes]);


  // Enumerar monitores disponibles usando Electron
  useEffect(() => {
    const loadMonitors = async () => {
      if ((window as any).electronAPI?.getDisplays) {
        try {
          const displays = await (window as any).electronAPI.getDisplays();
          const mapped: MonitorInfo[] = displays.map((d: any) => {
            const scale = d.scaleFactor || 1;
            const width = d.bounds.width * scale;
            const height = d.bounds.height * scale;
            return {
              id: d.id.toString(),
              label: `${d.label} (${width}x${height})`,
              position: { x: d.bounds.x, y: d.bounds.y },
              size: { width, height },
              isPrimary: d.primary,
              scaleFactor: scale
            };
          });
          mapped.sort((a, b) => {
            if (a.isPrimary !== b.isPrimary) return a.isPrimary ? -1 : 1;
            return a.position.x - b.position.x;
          });
          setMonitors(mapped);
          setMonitorRoles(prev => {
            const roles: Record<string, 'main' | 'secondary' | 'none'> = {};
            mapped.forEach(m => {
              roles[m.id] = prev[m.id] || 'none';
            });
            if (!Object.values(roles).some(r => r === 'main')) {
              const primary = mapped.find(m => m.isPrimary) || mapped[0];
              if (primary) roles[primary.id] = 'main';
            }
            const newMain = Object.entries(roles).find(([, r]) => r === 'main')?.[0];
            if (newMain) setStartMonitor(newMain);
            return roles;
          });
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
      window.dispatchEvent(new Event('resize'));
    };
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

  useEffect(() => {
    window.dispatchEvent(new Event('resize'));
  }, [isFullscreenMode]);

  useEffect(() => {
    const api = (window as any).electronAPI;
    if (!api?.onMainLeaveFullscreen) return;
    const handler = () => {
      setIsFullscreenMode(false);
      engineRef.current?.setMultiMonitorMode(false);
      localStorage.setItem('multiMonitorMode', 'false');
    };
    api.onMainLeaveFullscreen(handler);
    return () => {
      api.removeMainLeaveFullscreenListener?.();
    };
  }, []);

  // Inicializar el engine
  useEffect(() => {
    // Solo inicializar el engine cuando el usuario esté en el modo Audiovisualizer
    if (currentApp !== 'audiovisualizer') {
      return;
    }

    const initEngine = async () => {
      if (!canvasRef.current) {
        console.error('❌ Canvas ref is null');
        return;
      }

      console.log('🔧 Canvas found, initializing engine...');
      try {
        setStatus('Loading presets...');
        const engine = new AudioVisualizerEngine(canvasRef.current, { glitchTextPads, visualsPath });
        await engine.initialize();
        engineRef.current = engine;
        setGenLabBasePreset(engine.getGenLabBasePreset());
        setFractalLabBasePreset(engine.getFractalLabBasePreset());

        const multiMonitor = localStorage.getItem('multiMonitorMode') === 'true';
        engine.setMultiMonitorMode(multiMonitor);

        let presets = engine.getAvailablePresets();
        if (customTextContents.length > 0) {
          presets = await engine.updateCustomTextTemplates(glitchTextPads, customTextContents);
        }
        if (genLabPresets.length > 0) {
          presets = await engine.updateGenLabPresets(genLabPresets);
        }
        if (fractalLabPresets.length > 0) {
          presets = await engine.updateFractalLabPresets(fractalLabPresets);
        }
        setAvailablePresets(presets);
        setIsInitialized(true);
        setStatus('Ready');
        console.log(`✅ Engine initialized with ${presets.length} presets`);
      } catch (error) {
        console.error('❌ Failed to initialize engine:', error);
        setStatus('Error during initialization');
      }
    };

    console.log('🚀 Starting app initialization...');
    initEngine();

    return () => {
      if (engineRef.current) {
        engineRef.current.dispose();
      }
    };
  }, [currentApp, glitchTextPads, visualsPath]);


  // Activar capas almacenadas en modo fullscreen
  useEffect(() => {
    if (isFullscreenMode && isInitialized && engineRef.current) {
      const stored = localStorage.getItem('activeLayers');
      if (stored) {
        const layers = JSON.parse(stored) as Record<string, string>;
        Promise.all(
          Object.entries(layers).map(([layerId, presetId]) =>
            engineRef.current!.activateLayerPreset(layerId, presetId)
          )
        ).catch(err => {
          console.error('Failed to activate stored layers', err);
        });
      }
    }
  }, [isFullscreenMode, isInitialized]);

  // Cerrar ventana fullscreen con ESC o hotkey configurable
  useEffect(() => {
    if (isFullscreenMode) {
      const handler = (e: KeyboardEvent) => {
        if (
          e.key === 'Escape' ||
          e.key.toUpperCase() === exitFullscreenHotkey.toUpperCase()
        ) {
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
  }, [isFullscreenMode, exitFullscreenHotkey]);

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

  // Recalcular el tamano del canvas al mostrar/ocultar la UI
  useEffect(() => {
    window.dispatchEvent(new Event('resize'));
  }, [isUiHidden]);

  // Funcion de debug para verificar el grid completo
  const debugLaunchpadGrid = () => {
    if (!launchpadOutput) {
      console.log('No hay Launchpad conectado');
      return;
    }

    console.log('🔍 Test de debug del grid completo 8x8...');

    // Test secuencial de todos los pads
    for (let i = 0; i < 64; i++) {
      setTimeout(() => {
        const row = Math.floor(i / 8);
        const col = i % 8;
        const note = gridIndexToNote(i);
        console.log(`Encendiendo pad ${i} (fila ${row}, columna ${col}, nota ${note})`);

        launchpadOutput.send([0x90, note, 60 + (i % 64)]);

        setTimeout(() => {
          launchpadOutput.send([0x90, note, 0]);
        }, 100);

      }, i * 50);
    }
  };

  // Exponer funcion de debug globalmente
  (window as any).debugLaunchpadGrid = debugLaunchpadGrid;

  // Handlers
  const handleFullScreen = useCallback(async () => {
    if ((window as any).electronAPI) {
      localStorage.setItem('activeLayers', JSON.stringify(activeLayers));
      const mainId = Object.entries(monitorRoles).find(([, role]) => role === 'main')?.[0];
      const secondaryIds = Object.entries(monitorRoles)
        .filter(([, role]) => role === 'secondary')
        .map(([id]) => id);
      const ids = [
        ...(mainId !== undefined ? [parseInt(mainId, 10)] : []),
        ...secondaryIds.map(id => parseInt(id, 10))
      ].filter(id => !Number.isNaN(id));
      if (ids.length === 0) {
        setStatus('Error: No monitors selected');
        return;
      }
      if (isFullscreenMode) {
        engineRef.current?.setMultiMonitorMode(false);
        localStorage.setItem('multiMonitorMode', 'false');
      } else {
        const multi = ids.length > 1;
        engineRef.current?.setMultiMonitorMode(multi);
        localStorage.setItem('multiMonitorMode', multi ? 'true' : 'false');
      }
      try {
        await (window as any).electronAPI.toggleFullscreen(ids);
        setStatus(`Fullscreen toggled en ${ids.length} monitor(es)`);
        setIsFullscreenMode(!isFullscreenMode);
      } catch (err) {
        console.error('Fullscreen error:', err);
        setStatus('Error: Fullscreen could not be enabled');
      }
    } else if ((window as any).__TAURI__) {
      localStorage.setItem('activeLayers', JSON.stringify(activeLayers));

      try {
        const { WebviewWindow } = await import(
          /* @vite-ignore */ '@tauri-apps/api/window'
        );

        let activeMonitors = monitors.filter(
          m => monitorRoles[m.id] === 'main' || monitorRoles[m.id] === 'secondary'
        );
        const mainId = Object.entries(monitorRoles).find(([, role]) => role === 'main')?.[0];
        if (mainId) {
          const idx = activeMonitors.findIndex(m => m.id === mainId);
          if (idx > 0) {
            const [main] = activeMonitors.splice(idx, 1);
            activeMonitors.unshift(main);
          }
        }

        if (activeMonitors.length === 0) {
          setStatus('Error: No monitors selected');
          return;
        }
        if (isFullscreenMode) {
          engineRef.current?.setMultiMonitorMode(false);
          localStorage.setItem('multiMonitorMode', 'false');
        } else {
          const multi = activeMonitors.length > 1;
          engineRef.current?.setMultiMonitorMode(multi);
          localStorage.setItem('multiMonitorMode', multi ? 'true' : 'false');
        }

        console.log(`🎯 Abriendo fullscreen en ${activeMonitors.length} monitores`);

        activeMonitors.forEach((monitor, index) => {
          const label = `fullscreen-${monitor.id}-${Date.now()}-${index}`;

          const windowOptions = {
            url: `index.html?fullscreen=true&monitor=${monitor.id}`,
            x: monitor.position.x,
            y: monitor.position.y,
            width: monitor.size.width,
            height: monitor.size.height,
            decorations: false,
            fullscreen: fullscreenByDefault,
            skipTaskbar: true,
            resizable: false,
            title: `Visual Output - ${monitor.label}`,
            alwaysOnTop: false
          };

          console.log(`🖥️ Creando ventana en ${monitor.label}:`, windowOptions);

          try {
            new WebviewWindow(label, windowOptions);
          } catch (windowError) {
            console.error(`Error creating window for ${monitor.label}:`, windowError);
            setStatus(`Error: Could not create window on ${monitor.label}`);
          }
        });

        setStatus(`Fullscreen activo en ${activeMonitors.length} monitor(es)`);
        setIsFullscreenMode(!isFullscreenMode);
      } catch (err) {
        console.error('Fullscreen error:', err);
        setStatus('Error: Fullscreen could not be enabled');
      }
    } else {
      const elem: any = document.documentElement;
      if (elem.requestFullscreen) {
        await elem.requestFullscreen();
        setIsFullscreenMode(true);
        setStatus('Fullscreen activado (navegador)');
      } else {
        setStatus('Error: Fullscreen not available');
      }
    }
  }, [activeLayers, monitorRoles, monitors, isFullscreenMode]);

  useEffect(() => {
    if (isFullscreenMode) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key.toUpperCase() === fullscreenHotkey.toUpperCase()) {
        e.preventDefault();
        handleFullScreen();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleFullScreen, fullscreenHotkey, isFullscreenMode]);

  const handleClearAll = () => {
    if (!engineRef.current) return;
    ['A', 'B', 'C'].forEach(layerId => engineRef.current?.deactivateLayerPreset(layerId));
    engineRef.current.clearRenderer();
    setActiveLayers({});
    setSelectedPreset(null);
    setSelectedLayer(null);
    setClearSignal(prev => prev + 1);
    setStatus('Capas limpiadas');
    setLayerEffects(prev => ({
      A: { ...prev.A, active: prev.A.alwaysOn },
      B: { ...prev.B, active: prev.B.alwaysOn },
      C: { ...prev.C, active: prev.C.alwaysOn }
    }));
  };

  const handleToggleUi = () => {
    setIsUiHidden(prev => !prev);
  };

  const handleLayerEffectChange = (layerId: string, effect: string) => {
    setLayerEffects(prev => ({
      ...prev,
      [layerId]: { ...prev[layerId], effect, active: prev[layerId].alwaysOn }
    }));
  };

  const handleLayerEffectToggle = (layerId: string, alwaysOn: boolean) => {
    setLayerEffects(prev => ({
      ...prev,
      [layerId]: { ...prev[layerId], alwaysOn, active: alwaysOn }
    }));
  };

  const handleEffectMidiNoteChange = (effect: string, note: number) => {
    setEffectMidiNotes(prev => ({ ...prev, [effect]: note }));
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
        case 'midiTrigger': {
          setMidiTrigger(msg.data);
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

  const handleMonitorRoleChange = (id: string, role: 'main' | 'secondary' | 'none') => {
    setMonitorRoles(prev => {
      const updated = { ...prev, [id]: role } as Record<string, 'main' | 'secondary' | 'none'>;
      if (role === 'main') {
        Object.keys(updated).forEach(otherId => {
          if (otherId !== id && updated[otherId] === 'main') {
            updated[otherId] = 'secondary';
          }
        });
      }
      if (!Object.values(updated).some(r => r === 'main')) {
        const primaryMonitor = monitors.find(m => m.isPrimary) || monitors[0];
        if (primaryMonitor) {
          updated[primaryMonitor.id] = 'main';
        }
      }
      const newMain = Object.entries(updated).find(([, r]) => r === 'main')?.[0];
      if (newMain) {
        setStartMonitor(newMain);
      }
      return updated;
    });
  };

  // Handler para cambios en los templates de custom text
  const handleCustomTextTemplateChange = async (count: number, texts: string[]) => {
    setGlitchTextPads(count);
    setCustomTextContents(texts);
    localStorage.setItem('glitchTextPads', count.toString());
    localStorage.setItem('customTextTemplate', JSON.stringify({ count, texts }));

    if (engineRef.current) {
      try {
        const updatedPresets = await engineRef.current.updateCustomTextTemplates(count, texts);
        setAvailablePresets(updatedPresets);
        setStatus(`Custom text actualizado: ${count} instancia${count > 1 ? 's' : ''}`);
      } catch (error) {
        console.error('Error updating custom text templates:', error);
        setStatus('Error updating custom text');
      }
    }
  };

  const handleCustomTextCountChange = (count: number) => {
    handleCustomTextTemplateChange(count, customTextContents);
  };

  const handleGenLabPresetsChange = async (presets: { name: string; config: any }[]) => {
    setGenLabPresets(presets);
    localStorage.setItem('genLabPresets', JSON.stringify(presets));
    if (engineRef.current) {
      try {
        const updated = await engineRef.current.updateGenLabPresets(presets);
        setAvailablePresets(updated);
        setStatus(`Gen Lab actualizado: ${presets.length} preset${presets.length !== 1 ? 's' : ''}`);
      } catch (err) {
        console.error('Error updating Gen Lab presets:', err);
        setStatus('Error updating Gen Lab');
      }
    }
  };

  const handleFractalLabPresetsChange = async (presets: { name: string; config: any }[]) => {
    setFractalLabPresets(presets);
    localStorage.setItem('fractalLabPresets', JSON.stringify(presets));
    if (engineRef.current) {
      try {
        const updated = await engineRef.current.updateFractalLabPresets(presets);
        setAvailablePresets(updated);
        setStatus(`Fractal Lab actualizado: ${presets.length} preset${presets.length !== 1 ? 's' : ''}`);
      } catch (err) {
        console.error('Error updating Fractal Lab presets:', err);
        setStatus('Error updating Fractal Lab');
      }
    }
  };

  // Handler para anadir preset a layer desde la galeria sin activarlo
  const handleAddPresetToLayer = (presetId: string, layerId: string) => {
    const addFn = (window as any).addPresetToLayer as
      | ((layerId: string, presetId: string) => void)
      | undefined;

    if (typeof addFn !== 'function') return;

    addFn(layerId, presetId);

    const preset = availablePresets.find(p => p.id === presetId);
    if (preset) {
      setStatus(`${preset.config.name} added to Layer ${layerId}`);
    }
  };

  const handleRemovePresetFromLayer = (presetId: string, layerId: string) => {
    const removeFn = (window as any).removePresetFromLayer as
      | ((layerId: string, presetId: string) => void)
      | undefined;

    if (typeof removeFn !== 'function') return;

    removeFn(layerId, presetId);

    const preset = availablePresets.find(p => p.id === presetId);
    if (preset) {
      setStatus(`${preset.config.name} removed from Layer ${layerId}`);
    }
  };

  const getCurrentPresetName = (): string => {
    if (!selectedPreset) return 'None';
    return `${selectedPreset.config.name} (${selectedLayer || 'N/A'})`;
  };

  const handleSelectApp = (app: AppMode) => {
    setCurrentApp(app);
    localStorage.setItem('jungle-lab-preferred-app', app);
  };

  const handleSwitchApp = (app: AppMode) => {
    setCurrentApp(app);
  };

  // Show app selector if no app is selected
  if (!currentApp) {
    return <AppSelector onSelectApp={handleSelectApp} />;
  }

  // Show Crea Lab
  if (currentApp === 'crealab') {
    return (
      <div className="app-container crealab-app">
        <CreaLab onSwitchToAudioVisualizer={() => handleSwitchApp('audiovisualizer')} />
      </div>
    );
  }

  const midiDeviceName = midiDeviceId ? midiDevices.find((d: any) => d.id === midiDeviceId)?.name || null : null;
  const launchpadAvailable = launchpadOutputs.length > 0;
  const audioDeviceName = audioDeviceId ? audioDevices.find(d => d.deviceId === audioDeviceId)?.label || null : null;
  const audioLevel = Math.min((audioData.low + audioData.mid + audioData.high) / 3, 1);

  return (
    <div className={`app-container audiovisualizer-app ${isUiHidden ? 'ui-hidden' : ''}`}>
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
        onToggleUi={handleToggleUi}
        onClearAll={handleClearAll}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenResources={() => setResourcesOpen(true)}
        launchpadAvailable={launchpadAvailable}
        launchpadRunning={launchpadRunning}
        launchpadPreset={launchpadPreset}
        onToggleLaunchpad={() => setLaunchpadRunning(r => !r)}
        launchpadText={launchpadText}
        onLaunchpadTextChange={setLaunchpadText}
        onSwitchToCreaLab={() => handleSwitchApp('crealab')}
        onLaunchpadPresetChange={setLaunchpadPreset}
      />

      {/* Grid de capas */}
      <div className="layer-grid-container">
        <LayerGrid
          presets={availablePresets}
          externalTrigger={midiTrigger}
          onPresetActivate={(layerId, presetId, velocity) => {
            (async () => {
              if (engineRef.current) {
                await engineRef.current.activateLayerPreset(layerId, presetId);
                setActiveLayers(prev => ({ ...prev, [layerId]: presetId }));

                const preset = availablePresets.find(p => p.id === presetId);
                if (preset) {
                  const existing = layerPresetConfigs[layerId]?.[presetId];
                  if (existing) {
                    applyPresetConfig(engineRef.current, layerId, existing);
                  } else {
                    const cfg = await engineRef.current.getLayerPresetConfig(layerId, presetId);
                    setLayerPresetConfigs(prev => ({
                      ...prev,
                      [layerId]: { ...(prev[layerId] || {}), [presetId]: cfg }
                    }));
                  }
                  setSelectedPreset(preset);
                  setSelectedLayer(layerId);
                }
              }
            })();
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
            (async () => {
              if (presetId) {
                const preset = availablePresets.find(p => p.id === presetId);
                if (preset) {
                  const existing = layerPresetConfigs[layerId]?.[presetId];
                  if (!existing) {
                    const cfg = await engineRef.current?.getLayerPresetConfig(layerId, presetId);
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
            })();
          }}
          clearAllSignal={clearSignal}
          layerChannels={layerChannels}
          layerEffects={layerEffects}
          onLayerEffectChange={handleLayerEffectChange}
          onLayerEffectToggle={handleLayerEffectToggle}
          onOpenResources={() => setResourcesOpen(true)}
          bpm={bpm}
        />
      </div>

      {/* Seccion inferior con visuales y controles */}
      <div className="bottom-section">
        <div
          className="visual-wrapper"
          style={{ background: canvasBackground }}
        >
          <canvas
            ref={canvasRef}
            className={`main-canvas ${activeEffectClasses}`}
            style={{
              filter: `brightness(${canvasBrightness}) saturate(${canvasVibrance})`
            }}
          />
        </div>
        {!isResourcesOpen && (
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
                onChange={(path, value) => {
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
        )}
      </div>

      {/* Barra de estado */}
      <StatusBar
        status={status}
        fps={fps}
        currentPreset={getCurrentPresetName()}
        audioData={audioData}
      />

      {/* Modal de configuracion global */}
      <GlobalSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        audioDevices={audioDevices.map(d => ({ id: d.deviceId, label: d.label || d.deviceId }))}
        midiDevices={midiDevices.map((d: any) => ({ id: d.id, label: d.name || d.id }))}
        launchpadDevices={launchpadOutputs.map((d: any) => ({ id: d.id, label: d.name || d.id }))}
        selectedAudioId={audioDeviceId}
        selectedMidiId={midiDeviceId}
        selectedLaunchpadId={launchpadId}
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
        onSelectLaunchpad={(id) => {
          setLaunchpadId(id);
          if (id) {
            localStorage.setItem('launchpadId', id);
          } else {
            localStorage.removeItem('launchpadId');
          }
        }}
        audioGain={audioGain}
        onAudioGainChange={setAudioGain}
        midiClockSettings={midiClockSettings}
        onUpdateClockSettings={updateClockSettings}
        internalBpm={internalBpm}
        onSetInternalBpm={setInternalBpm}
        clockStable={clockStable}
        currentMeasure={currentMeasure}
        currentBeat={currentBeat}
        layerChannels={layerChannels}
        onLayerChannelChange={(layerId, channel) => {
          const updated = { ...layerChannels, [layerId]: channel };
          setLayerChannels(updated);
          localStorage.setItem('layerMidiChannels', JSON.stringify(updated));
        }}
        effectMidiNotes={effectMidiNotes}
        onEffectMidiNoteChange={handleEffectMidiNoteChange}
        launchpadChannel={launchpadChannel}
        onLaunchpadChannelChange={setLaunchpadChannel}
        launchpadNote={launchpadNote}
        onLaunchpadNoteChange={setLaunchpadNote}
        launchpadSmoothness={launchpadSmoothness}
        onLaunchpadSmoothnessChange={setLaunchpadSmoothness}
        monitors={monitors}
        monitorRoles={monitorRoles}
        onMonitorRoleChange={handleMonitorRoleChange}
        startMonitor={startMonitor}
        onStartMonitorChange={setStartMonitor}
        glitchTextPads={glitchTextPads}
        onGlitchPadChange={handleCustomTextCountChange}
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
        fullscreenHotkey={fullscreenHotkey}
        onFullscreenHotkeyChange={(key) => {
          setFullscreenHotkey(key);
          localStorage.setItem('fullscreenHotkey', key);
        }}
        exitFullscreenHotkey={exitFullscreenHotkey}
        onExitFullscreenHotkeyChange={(key) => {
          setExitFullscreenHotkey(key);
          localStorage.setItem('exitFullscreenHotkey', key);
        }}
        fullscreenByDefault={fullscreenByDefault}
        onFullscreenByDefaultChange={(value) => {
          setFullscreenByDefault(value);
          localStorage.setItem('fullscreenByDefault', value.toString());
        }}
        canvasBrightness={canvasBrightness}
        onCanvasBrightnessChange={setCanvasBrightness}
        canvasVibrance={canvasVibrance}
        onCanvasVibranceChange={setCanvasVibrance}
        canvasBackground={canvasBackground}
        onCanvasBackgroundChange={setCanvasBackground}
        visualsPath={visualsPath}
        onVisualsPathChange={setVisualsPath}
      />

      {/* Modal de galeria de presets */}
      <ResourcesModal
        isOpen={isResourcesOpen}
        onClose={() => setResourcesOpen(false)}
        presets={availablePresets}
        onCustomTextTemplateChange={handleCustomTextTemplateChange}
        customTextTemplate={{ count: glitchTextPads, texts: customTextContents }}
        genLabPresets={genLabPresets}
        genLabBasePreset={genLabBasePreset}
        onGenLabPresetsChange={handleGenLabPresetsChange}
        fractalLabPresets={fractalLabPresets}
        fractalLabBasePreset={fractalLabBasePreset}
        onFractalLabPresetsChange={handleFractalLabPresetsChange}
        onAddPresetToLayer={handleAddPresetToLayer}
        onRemovePresetFromLayer={handleRemovePresetFromLayer}
        launchpadPresets={LAUNCHPAD_PRESETS}
        launchpadPreset={launchpadPreset}
        onLaunchpadPresetChange={setLaunchpadPreset}
        launchpadRunning={launchpadRunning}
        onToggleLaunchpad={() => setLaunchpadRunning(r => !r)}
        launchpadText={launchpadText}
        onLaunchpadTextChange={setLaunchpadText}
      />
    </div>
  );
};

export default App;