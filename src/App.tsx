// App.tsx - Correctly refactored with MidiContextProvider

import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  Suspense,
  lazy,
} from 'react';
import { AudioVisualizerEngine } from './core/AudioVisualizerEngine';
import { StatusBar } from './components/StatusBar';
import { TopBar } from './components/TopBar';
// Lazy loaded heavy components
const LayerGrid = lazy(() => import('./components/LayerGrid'));
const PresetControls = lazy(() => import('./components/PresetControls'));
const ResourcesModal = lazy(() => import('./components/ResourcesModal'));
const GlobalSettingsModal = lazy(() => import('./components/GlobalSettingsModal'));
import { LoadedPreset } from './core/PresetLoader';
import { setNestedValue } from './utils/objectPath';
import { AVAILABLE_EFFECTS } from './utils/effects';
import { gridIndexToNote, LAUNCHPAD_PRESETS } from './utils/launchpad';
import { useAudio } from './hooks/useAudio';
import { useLaunchpad } from './hooks/useLaunchpad';
import {
  MidiContextProvider,
  useMidiContext,
} from './contexts/MidiContext';
import './App.css';
import './AppLayout.css';
import VideoControls from './components/VideoControls';
import ResourceExplorer from './components/ResourceExplorer';
import {
  VideoResource,
  VideoPlaybackSettings,
  DEFAULT_VIDEO_PLAYBACK_SETTINGS,
} from './types/video';
import {
  loadVideoGallery,
  clearVideoGalleryCache,
  VideoProviderSettings,
  VideoProviderId,
} from './utils/videoProviders';
import { clearVideoCache } from './utils/videoCache';
import { useMidi } from './hooks/useMidi';

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  isPrimary: boolean;
  scaleFactor: number;
}

const RESOURCE_EXPLORER_WIDTH = 320;

const App: React.FC = () => {
  const playgroundRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<AudioVisualizerEngine | null>(null);
  const broadcastRef = useRef<BroadcastChannel | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [availablePresets, setAvailablePresets] = useState<LoadedPreset[]>([]);
  const [fps, setFps] = useState(60);
  const [status, setStatus] = useState('Initializing...');
  const [activeLayers, setActiveLayers] = useState<Record<string, string>>({});
  const [selectedPreset, setSelectedPreset] = useState<LoadedPreset | null>(null);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);
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

  const defaultVideoProviderSettings: VideoProviderSettings = {
    provider: 'pexels',
    apiKey: '',
    refreshMinutes: 30,
    query: 'vj loop',
  };

  const [videoProviderSettings, setVideoProviderSettings] = useState<VideoProviderSettings>(() => {
    try {
      const stored = localStorage.getItem('videoProviderSettings');
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          provider: (parsed.provider as VideoProviderId) || 'pexels',
          apiKey: parsed.apiKey || '',
          refreshMinutes: parsed.refreshMinutes || 30,
          query: parsed.query || 'vj loop',
        };
      }
    } catch (err) {
      console.warn('Unable to restore video provider settings', err);
    }
    return defaultVideoProviderSettings;
  });

  const [videoGallery, setVideoGallery] = useState<VideoResource[]>(() => {
    try {
      const cached = localStorage.getItem('videoGalleryCache');
      if (cached) {
        const parsed = JSON.parse(cached);
        return Array.isArray(parsed.items) ? parsed.items : [];
      }
    } catch {
      /* ignore */
    }
    return [];
  });
  const [isRefreshingVideos, setIsRefreshingVideos] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoResource | null>(null);
  const [selectedVideoLayer, setSelectedVideoLayer] = useState<string | null>(null);
  const [layerVideoSettings, setLayerVideoSettings] = useState<Record<string, VideoPlaybackSettings>>(() => {
    try {
      const stored = localStorage.getItem('layerVideoSettings');
      if (stored) {
        const parsed = JSON.parse(stored);
        return {
          A: { ...DEFAULT_VIDEO_PLAYBACK_SETTINGS, ...(parsed.A || {}) },
          B: { ...DEFAULT_VIDEO_PLAYBACK_SETTINGS, ...(parsed.B || {}) },
          C: { ...DEFAULT_VIDEO_PLAYBACK_SETTINGS, ...(parsed.C || {}) },
        };
      }
    } catch {
      /* ignore */
    }
    return {
      A: { ...DEFAULT_VIDEO_PLAYBACK_SETTINGS },
      B: { ...DEFAULT_VIDEO_PLAYBACK_SETTINGS },
      C: { ...DEFAULT_VIDEO_PLAYBACK_SETTINGS },
    };
  });

  const layerVideoSettingsRef = useRef(layerVideoSettings);
  const videoGalleryRef = useRef(videoGallery);

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

  const [layerVFX, setLayerVFX] = useState<Record<string, Record<string, string[]>>>(() => {
    try {
      const stored = localStorage.getItem('layerVFX');
      if (stored) return JSON.parse(stored);
    } catch {}
    return { A: {}, B: {}, C: {} };
  });

  const [isFullscreenMode, setIsFullscreenMode] = useState(
    () => new URLSearchParams(window.location.search).get('fullscreen') === 'true'
  );

  const midiProps = {
    isFullscreenMode,
    availablePresets,
    layerChannels,
    layerEffects,
    setLayerEffects,
    effectMidiNotes,
    engineRef,
  };

  return (
    <MidiContextProvider {...midiProps}>
      <AppContent
        {...{
          playgroundRef,
          canvasRef,
          engineRef,
          broadcastRef,
          isInitialized,
          setIsInitialized,
          availablePresets,
          setAvailablePresets,
          fps,
          setFps,
          status,
          setStatus,
          activeLayers,
          setActiveLayers,
          selectedPreset,
          setSelectedPreset,
          selectedLayer,
          setSelectedLayer,
          layerPresetConfigs,
          setLayerPresetConfigs,
          genLabPresets,
          setGenLabPresets,
          genLabBasePreset,
          setGenLabBasePreset,
          fractalLabPresets,
          setFractalLabPresets,
          fractalLabBasePreset,
          setFractalLabBasePreset,
          videoProviderSettings,
          setVideoProviderSettings,
          videoGallery,
          setVideoGallery,
          isRefreshingVideos,
          setIsRefreshingVideos,
          selectedVideo,
          setSelectedVideo,
          selectedVideoLayer,
          setSelectedVideoLayer,
          layerVideoSettings,
          setLayerVideoSettings,
          layerVideoSettingsRef,
          videoGalleryRef,
          layerChannels,
          setLayerChannels,
          effectMidiNotes,
          setEffectMidiNotes,
          layerEffects,
          setLayerEffects,
          layerVFX,
          setLayerVFX,
          isFullscreenMode,
          setIsFullscreenMode,
        }}
      />
    </MidiContextProvider>
  );
};

const AppContent: React.FC<any> = (props) => {
  const {
    playgroundRef,
    canvasRef,
    engineRef,
    broadcastRef,
    isInitialized,
    setIsInitialized,
    availablePresets,
    setAvailablePresets,
    fps,
    setFps,
    status,
    setStatus,
    activeLayers,
    setActiveLayers,
    selectedPreset,
    setSelectedPreset,
    selectedLayer,
    setSelectedLayer,
    layerPresetConfigs,
    setLayerPresetConfigs,
    genLabPresets,
    setGenLabPresets,
    genLabBasePreset,
    setGenLabBasePreset,
    fractalLabPresets,
    setFractalLabPresets,
    fractalLabBasePreset,
    setFractalLabBasePreset,
    videoProviderSettings,
    setVideoProviderSettings,
    videoGallery,
    setVideoGallery,
    isRefreshingVideos,
    setIsRefreshingVideos,
    selectedVideo,
    setSelectedVideo,
    selectedVideoLayer,
    setSelectedVideoLayer,
    layerVideoSettings,
    setLayerVideoSettings,
    layerVideoSettingsRef,
    videoGalleryRef,
    layerChannels,
    setLayerChannels,
    effectMidiNotes,
    setEffectMidiNotes,
    layerEffects,
    setLayerEffects,
    layerVFX,
    setLayerVFX,
    isFullscreenMode,
    setIsFullscreenMode,
  } = props;

  const urlParams = new URLSearchParams(window.location.search);
  const windowMode = urlParams.get('mode') || 'single';
  const isControlWindow = windowMode === 'control';
  const isVisualWindow = windowMode === 'visual';

  const [outputMode, setOutputMode] = useState<'standard' | 'vertical'>(() => {
    const saved = localStorage.getItem('outputMode');
    return (saved === 'vertical' ? 'vertical' : 'standard') as 'standard' | 'vertical';
  });

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

  const updateVideoProviderSettings = useCallback(
    (updates: Partial<VideoProviderSettings>) => {
      setVideoProviderSettings((prev: any) => ({ ...prev, ...updates }));
    },
    [setVideoProviderSettings]
  );

  const refreshVideoGallery = useCallback(
    async (force = false) => {
      setIsRefreshingVideos(true);
      try {
        const videos = await loadVideoGallery(videoProviderSettings, force);
        setVideoGallery(videos);
        if (engineRef.current) {
          engineRef.current.setVideoRegistry(videos);
        }
        setStatus(`Video gallery updated (${videos.length} items)`);
      } catch (error) {
        console.error('Failed to refresh video gallery', error);
        setStatus('Error loading video gallery');
      } finally {
        setIsRefreshingVideos(false);
      }
    },
    [videoProviderSettings, setIsRefreshingVideos, setVideoGallery, setStatus, engineRef]
  );

  const handleClearVideoCache = useCallback(async () => {
    try {
      clearVideoGalleryCache();
      await clearVideoCache();
      setVideoGallery([]);
      setStatus('Video cache cleared');
      await refreshVideoGallery(true);
    } catch (error) {
      console.error('Failed to clear video cache', error);
      setStatus('Error clearing video cache');
    }
  }, [refreshVideoGallery, setVideoGallery, setStatus]);

  const handleVideoSettingsChange = useCallback(
    (updates: Partial<VideoPlaybackSettings>) => {
      if (!selectedVideoLayer) return;
      setLayerVideoSettings((prev: any) => {
        const current = prev[selectedVideoLayer] || DEFAULT_VIDEO_PLAYBACK_SETTINGS;
        return {
          ...prev,
          [selectedVideoLayer]: { ...current, ...updates },
        };
      });
      if (engineRef.current) {
        engineRef.current.updateLayerVideoSettings(selectedVideoLayer, updates);
      }
    },
    [selectedVideoLayer, setLayerVideoSettings, engineRef]
  );

  const handleAddVideoToLayer = useCallback(
    (videoId: string, layerId: string) => {
      const video = videoGalleryRef.current.find((item: any) => item.id === videoId);
      if (video) {
        setStatus(`${video.title} assigned to Layer ${layerId}`);
      }
    },
    [videoGalleryRef, setStatus]
  );

  const handleRemoveVideoFromLayer = useCallback((videoId: string, layerId: string) => {
    const video = videoGalleryRef.current.find((item: any) => item.id === videoId);
    if (video) {
      setStatus(`${video.title} removed from Layer ${layerId}`);
    }
  }, [videoGalleryRef, setStatus]);

  const handleLaunchpadToggle = useCallback(() => {
    console.log('🎯 LaunchPad toggle requested');

    if (!launchpadOutput) {
      console.warn('⚠️ No LaunchPad device available for toggle');
      return;
    }

    if (launchpadOutput.state !== 'connected') {
      console.warn('⚠️ LaunchPad device not connected:', launchpadOutput.state);
      return;
    }

    console.log('✅ LaunchPad toggle válido, ejecutando...');
    setLaunchpadRunning((prev: any) => {
      const newState = !prev;
      console.log(`🔄 LaunchPad state: ${prev} → ${newState}`);
      return newState;
    });
  }, [launchpadOutput, setLaunchpadRunning]);

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
  } = useMidiContext();

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
  const [emptyPads, setEmptyPads] = useState<number>(() => parseInt(localStorage.getItem('emptyPads') || '1'));
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
  }, [broadcastRef]);

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
  }, [setAudioDeviceId, setMidiDeviceId]);

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
    try {
      localStorage.setItem('videoProviderSettings', JSON.stringify(videoProviderSettings));
    } catch (err) {
      console.warn('Failed to persist video provider settings:', err);
    }
  }, [videoProviderSettings]);

  useEffect(() => {
    try {
      localStorage.setItem('layerVideoSettings', JSON.stringify(layerVideoSettings));
    } catch (err) {
      console.warn('Failed to persist layer video settings:', err);
    }
    if (engineRef.current) {
      Object.entries(layerVideoSettings).forEach(([layerId, settings]) => {
        engineRef.current?.updateLayerVideoSettings(layerId, settings);
      });
    }
  }, [layerVideoSettings]);

  useEffect(() => {
    if (!isFullscreenMode && midiTrigger) {
      broadcastRef.current?.postMessage({ type: 'midiTrigger', data: midiTrigger });
    }
  }, [midiTrigger, isFullscreenMode, broadcastRef]);

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
      monitorId: startMonitor || undefined
    });
  }, [startMaximized, startMonitor]);

  useEffect(() => {
    refreshVideoGallery();
  }, [refreshVideoGallery]);

  useEffect(() => {
    if (!videoProviderSettings.refreshMinutes) return;
    const interval = window.setInterval(() => {
      refreshVideoGallery();
    }, videoProviderSettings.refreshMinutes * 60_000);
    return () => window.clearInterval(interval);
  }, [videoProviderSettings.refreshMinutes, refreshVideoGallery]);

  useEffect(() => {
    if (engineRef.current) {
      engineRef.current.setVideoRegistry(videoGallery);
    }
  }, [videoGallery, engineRef]);

  useEffect(() => {
    try {
      localStorage.setItem('layerPresetConfigs', JSON.stringify(layerPresetConfigs));
      broadcastRef.current?.postMessage({ type: 'layerPresetConfigs', data: layerPresetConfigs });
    } catch (e) {
      console.warn('Failed to persist layer preset configs:', e);
    }
  }, [layerPresetConfigs, broadcastRef]);

  useEffect(() => {
    try {
      localStorage.setItem('layerEffects', JSON.stringify(layerEffects));
    } catch (e) {
      console.warn('Failed to persist layer effects:', e);
    }
  }, [layerEffects]);

  useEffect(() => {
    try {
      localStorage.setItem('layerVFX', JSON.stringify(layerVFX));
    } catch (e) {
      console.warn('Failed to persist layer VFX:', e);
    }
  }, [layerVFX]);

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

  const refreshMonitors = useCallback(async () => {
    try {
      let mapped: MonitorInfo[] = [];

      if ((window as any).electronAPI?.getDisplays) {
        const displays = await (window as any).electronAPI.getDisplays();
        mapped = displays.map((d: any) => {
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
      } else if ((window as any).__TAURI__) {
        const { availableMonitors, primaryMonitor } = await import('@tauri-apps/api/window');
        const [displays, primary] = await Promise.all([
          availableMonitors(),
          primaryMonitor()
        ]);
        mapped = displays.map((d: any, index: number) => {
          const width = d.size.width;
          const height = d.size.height;
          const id = `${d.name || 'monitor'}-${index}`;
          return {
            id,
            label: `${d.name || `Monitor ${index + 1}`} (${width}x${height})`,
            position: { x: d.position.x, y: d.position.y },
            size: { width, height },
            isPrimary: primary ? d.name === primary.name : index === 0,
            scaleFactor: d.scaleFactor || 1
          };
        });
      } else {
        const width = window.screen.width;
        const height = window.screen.height;
        mapped = [{
          id: 'screen',
          label: `Screen (${width}x${height})`,
          position: { x: 0, y: 0 },
          size: { width, height },
          isPrimary: true,
          scaleFactor: window.devicePixelRatio || 1
        }];
      }

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
  }, [setMonitors, setMonitorRoles, setStartMonitor]);

  useEffect(() => {
    refreshMonitors();
  }, [refreshMonitors]);

  useEffect(() => {
    if (isSettingsOpen) refreshMonitors();
  }, [isSettingsOpen, refreshMonitors]);

  useEffect(() => {
    const handler = () => {
      const param = new URLSearchParams(window.location.search).get('fullscreen') === 'true';
      setIsFullscreenMode(param || !!document.fullscreenElement);
      window.dispatchEvent(new Event('resize'));
    };
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, [setIsFullscreenMode]);

  useEffect(() => {
    window.dispatchEvent(new Event('resize'));
  }, [isFullscreenMode]);

  useEffect(() => {
    if (isFullscreenMode) {
      setIsUiHidden(true);
    } else {
      setIsUiHidden(false);
    }
  }, [isFullscreenMode, setIsUiHidden]);

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
  }, [setIsFullscreenMode, engineRef]);

  useEffect(() => {
    const initEngine = async () => {
      if (isControlWindow) {
        console.log('🎛️ Control window: Loading preset list without engine...');
        try {
          setStatus('Loading preset list...');
          const tempDiv = document.createElement('div');
          const engine = new AudioVisualizerEngine(tempDiv, { glitchTextPads, visualsPath });
          await engine.initialize();

          let presets = engine.getAvailablePresets();
          if (emptyPads !== 1) {
            presets = await engine.updateEmptyTemplates(emptyPads);
          }
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
          setGenLabBasePreset(engine.getGenLabBasePreset());
          setFractalLabBasePreset(engine.getFractalLabBasePreset());

          engine.dispose();
          setIsInitialized(true);
          setStatus('Ready (Control Window)');
          console.log(`✅ Loaded ${presets.length} presets for control window`);
        } catch (error) {
          console.error('❌ Failed to load presets:', error);
          setStatus('Error loading presets');
        }
        return;
      }

      if (!playgroundRef.current) {
        console.error('❌ Playground ref is null');
        return;
      }

      console.log('🔧 Playground found, initializing engine...');
      try {
        setStatus('Loading presets...');
        const engine = new AudioVisualizerEngine(playgroundRef.current, { glitchTextPads, visualsPath });
        await engine.initialize();
        engineRef.current = engine;
        canvasRef.current = engine.getLayerCanvas('A') || null;
        setGenLabBasePreset(engine.getGenLabBasePreset());
        setFractalLabBasePreset(engine.getFractalLabBasePreset());

        engine.setVideoRegistry(videoGalleryRef.current);
        Object.entries(layerVideoSettingsRef.current).forEach(([layerId, settings]) => {
          engine.updateLayerVideoSettings(layerId, settings);
        });

        const multiMonitor = localStorage.getItem('multiMonitorMode') === 'true';
        engine.setMultiMonitorMode(multiMonitor);

        let presets = engine.getAvailablePresets();
        if (emptyPads !== 1) {
          presets = await engine.updateEmptyTemplates(emptyPads);
        }
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
  }, [glitchTextPads, visualsPath, isControlWindow, customTextContents, emptyPads, genLabPresets, fractalLabPresets, setAvailablePresets, setGenLabBasePreset, setFractalLabBasePreset, setIsInitialized, setStatus, engineRef, canvasRef, videoGalleryRef, layerVideoSettingsRef]);
  
  // ... the rest of the file
  
export default App;