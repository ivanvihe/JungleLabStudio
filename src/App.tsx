import React, { useEffect, useRef, useState } from 'react';
import { AudioVisualizerEngine } from './core/AudioVisualizerEngine';
import { LayerGrid } from './components/LayerGrid';
import { StatusBar } from './components/StatusBar';
import { PresetControls } from './components/PresetControls';
import { LoadedPreset, AudioData } from './core/PresetLoader';
import './App.css';
import './components/LayerGrid.css';

const App: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<AudioVisualizerEngine | null>(null);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [availablePresets, setAvailablePresets] = useState<LoadedPreset[]>([]);
  const [audioData, setAudioData] = useState<AudioData>({ low: 0, mid: 0, high: 0, fft: [] });
  const [fps, setFps] = useState(60);
  const [status, setStatus] = useState('Inicializando...');
  const [activeLayers, setActiveLayers] = useState<Record<string, string>>({});
  const [selectedPreset, setSelectedPreset] = useState<LoadedPreset | null>(null);
  const [selectedLayer, setSelectedLayer] = useState<string | null>(null);

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
        
        const engine = new AudioVisualizerEngine(canvasRef.current);
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

  // Configurar listener de audio - VERSIÓN MEJORADA
  useEffect(() => {
    const setupAudioListener = async () => {
      try {
        // Detectar si estamos en un entorno Tauri
        if (typeof window !== 'undefined' && (window as any).__TAURI__) {
          console.log('🎵 Tauri environment detected, setting up audio listener...');
          
          // Importación dinámica solo en entorno Tauri
          const tauriApi = await import('@tauri-apps/api/event');
          
          await tauriApi.listen('audio_data', (event) => {
            const data = event.payload as AudioData;
            setAudioData(data);

            if (engineRef.current) {
              engineRef.current.updateAudioData(data);
            }
          });
          
          console.log('✅ Tauri audio listener setup complete');
        } else {
          console.log('⚠️ Not in Tauri environment, audio listener disabled');
          
          // Opcional: Configurar datos de audio simulados para desarrollo
          const simulateAudioData = () => {
            const time = Date.now() * 0.001;
            const simulatedData: AudioData = {
              low: (Math.sin(time * 0.5) + 1) * 0.5,
              mid: (Math.sin(time * 1.2) + 1) * 0.5,
              high: (Math.sin(time * 2.0) + 1) * 0.5,
              fft: Array.from({ length: 256 }, (_, i) => 
                (Math.sin(time + i * 0.1) + 1) * 0.5
              )
            };
            
            setAudioData(simulatedData);
            
            if (engineRef.current) {
              engineRef.current.updateAudioData(simulatedData);
            }
          };
          
          // Simular datos de audio cada 16ms (~60fps)
          const interval = setInterval(simulateAudioData, 16);
          
          return () => clearInterval(interval);
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
        
        setAudioData(fallbackData);
        
        if (engineRef.current) {
          engineRef.current.updateAudioData(fallbackData);
        }
      }
    };

    if (isInitialized) {
      setupAudioListener();
    }
  }, [isInitialized]);

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

  return (
    <div className="app">
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
        {selectedPreset && (
          <div className="controls-panel">
            <PresetControls preset={selectedPreset} onConfigUpdate={handlePresetConfigUpdate} />
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
    </div>
  );
};

export default App;