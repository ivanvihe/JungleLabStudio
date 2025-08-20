import React, { useState, useEffect } from 'react';
import { LoadedPreset } from '../core/PresetLoader';

interface LayerConfig {
  id: string;
  name: string;
  color: string;
  midiChannel: number;
  fadeTime: number;
  opacity: number;
  activePreset: string | null;
}

interface LayerGridProps {
  presets: LoadedPreset[];
  onPresetActivate: (layerId: string, presetId: string) => void;
  onLayerClear: (layerId: string) => void;
  onLayerConfigChange: (layerId: string, config: Partial<LayerConfig>) => void;
  onPresetSelect: (layerId: string, presetId: string) => void;
  clearAllSignal: number;
  externalTrigger?: { layerId: string; presetId: string } | null;
  layerChannels: Record<string, number>;
}

export const LayerGrid: React.FC<LayerGridProps> = ({
  presets,
  onPresetActivate,
  onLayerClear,
  onLayerConfigChange,
  onPresetSelect,
  clearAllSignal,
  externalTrigger,
  layerChannels
}) => {
  const [layers, setLayers] = useState<LayerConfig[]>([
    { id: 'A', name: 'Layer A', color: '#FF6B6B', midiChannel: layerChannels.A || 14, fadeTime: 200, opacity: 100, activePreset: null },
    { id: 'B', name: 'Layer B', color: '#4ECDC4', midiChannel: layerChannels.B || 15, fadeTime: 200, opacity: 100, activePreset: null },
    { id: 'C', name: 'Layer C', color: '#45B7D1', midiChannel: layerChannels.C || 16, fadeTime: 200, opacity: 100, activePreset: null },
  ]);

  useEffect(() => {
    setLayers(prev => prev.map(layer => ({ ...layer, activePreset: null })));
    setClickedCell(null);
  }, [clearAllSignal]);

  const [clickedCell, setClickedCell] = useState<string | null>(null);

  const handlePresetClick = (layerId: string, presetId: string) => {
    const cellKey = `${layerId}-${presetId}`;
    const layer = layers.find(l => l.id === layerId);
    const wasActive = layer?.activePreset === presetId;
    const preset = presets.find(p => p.id === presetId);
    const isOneShot = preset?.config.category === 'one-shot';

    setClickedCell(cellKey);
    setTimeout(() => setClickedCell(null), 150);

    setLayers(prev => prev.map(l =>
      l.id === layerId
        ? { ...l, activePreset: presetId }
        : l
    ));

    if (!wasActive || isOneShot) {
      onPresetActivate(layerId, presetId);
    }
    onPresetSelect(layerId, presetId);
  };

  const handleLayerClear = (layerId: string) => {
    setLayers(prev => prev.map(layer => 
      layer.id === layerId 
        ? { ...layer, activePreset: null }
        : layer
    ));
    onLayerClear(layerId);

    // Limpiar selección de controles
    onPresetSelect(layerId, '');
  };

  const handleLayerConfigChange = (layerId: string, field: keyof LayerConfig, value: any) => {
    setLayers(prev => prev.map(layer => 
      layer.id === layerId 
        ? { ...layer, [field]: value }
        : layer
    ));
    
    const updatedLayer = layers.find(l => l.id === layerId);
    if (updatedLayer) {
      onLayerConfigChange(layerId, { [field]: value });
    }
  };

  useEffect(() => {
    if (externalTrigger) {
      handlePresetClick(externalTrigger.layerId, externalTrigger.presetId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [externalTrigger]);

  useEffect(() => {
    setLayers(prev => prev.map(layer => ({
      ...layer,
      midiChannel: layerChannels[layer.id] || layer.midiChannel
    })));
  }, [layerChannels]);

  const getPresetThumbnail = (preset: LoadedPreset): string => {
    // Generar thumbnail basado en categoría/tipo
    const thumbnails: Record<string, string> = {
      'neural_network': '🧠',
      'abstract-lines': '📈',
      'abstract-lines-pro': '📊',
      'abstract-shapes': '🔷',
      'evolutive-particles': '✨',
      'boom-wave': '💥',
      'plasma-ray': '⚡',
      'shot-text': '📝',
      'text-glitch': '🔤'
    };
    return thumbnails[preset.id] || '🎨';
  };

  return (
    <div className="layer-grid">
      {layers.map((layer) => (
        <div key={layer.id} className="layer-section">
          {/* Layer Controls - 100x100 square */}
          <div
            className="layer-sidebar"
            style={{ borderLeftColor: layer.color }}
          >
            <div className="layer-letter" style={{ color: layer.color }}>
              {layer.id}
            </div>
            <div className="midi-channel-label">CH {layer.midiChannel}</div>
            <div className="sidebar-controls">
              <input
                type="range"
                value={layer.opacity}
                onChange={(e) =>
                  handleLayerConfigChange(layer.id, 'opacity', parseInt(e.target.value))
                }
                className="opacity-slider"
                min="0"
                max="100"
              />
              <div className="fade-control">
                <input
                  type="number"
                  value={layer.fadeTime}
                  onChange={(e) =>
                    handleLayerConfigChange(
                      layer.id,
                      'fadeTime',
                      parseInt(e.target.value)
                    )
                  }
                  className="fade-input"
                  min="0"
                  max="5000"
                  step="50"
                />
                <span className="unit">ms</span>
              </div>
            </div>
          </div>

          {/* Preset Grid */}
          <div className="preset-grid">
            {presets.map((preset) => {
              const cellKey = `${layer.id}-${preset.id}`;
              const isActive = layer.activePreset === preset.id;
              const isClicked = clickedCell === cellKey;
              
              return (
                <div
                  key={cellKey}
                  className={`preset-cell ${isActive ? 'active' : ''} ${isClicked ? 'clicked' : ''}`}
                  onClick={() => handlePresetClick(layer.id, preset.id)}
                  style={{
                    '--layer-color': layer.color,
                    '--layer-color-alpha': layer.color + '20'
                  } as React.CSSProperties}
                >
                    {preset.config.note !== undefined && (
                      <div className="preset-note-badge">{preset.config.note}</div>
                    )}
                  <div className="preset-thumbnail">
                    {getPresetThumbnail(preset)}
                  </div>
                  <div className="preset-info">
                    <div className="preset-name">{preset.config.name}</div>
                    <div className="preset-details">
                      <span className="preset-category">{preset.config.category}</span>
                    </div>
                  </div>
                  
                  {isActive && (
                    <div 
                      className="active-indicator"
                      style={{ backgroundColor: layer.color }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
