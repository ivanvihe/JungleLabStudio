import React, { useState } from 'react';
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
}

export const LayerGrid: React.FC<LayerGridProps> = ({
  presets,
  onPresetActivate,
  onLayerClear,
  onLayerConfigChange
}) => {
  const [layers, setLayers] = useState<LayerConfig[]>([
    { id: 'A', name: 'Layer A', color: '#FF6B6B', midiChannel: 14, fadeTime: 200, opacity: 100, activePreset: null },
    { id: 'B', name: 'Layer B', color: '#4ECDC4', midiChannel: 15, fadeTime: 200, opacity: 100, activePreset: null },
    { id: 'C', name: 'Layer C', color: '#45B7D1', midiChannel: 16, fadeTime: 200, opacity: 100, activePreset: null },
  ]);

  const [clickedCell, setClickedCell] = useState<string | null>(null);

  const handlePresetClick = (layerId: string, presetId: string) => {
    const cellKey = `${layerId}-${presetId}`;
    setClickedCell(cellKey);
    
    // Animación de click
    setTimeout(() => setClickedCell(null), 150);
    
    // Actualizar capa activa
    setLayers(prev => prev.map(layer => 
      layer.id === layerId 
        ? { ...layer, activePreset: presetId }
        : layer
    ));
    
    onPresetActivate(layerId, presetId);
  };

  const handleLayerClear = (layerId: string) => {
    setLayers(prev => prev.map(layer => 
      layer.id === layerId 
        ? { ...layer, activePreset: null }
        : layer
    ));
    onLayerClear(layerId);
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

  const getPresetThumbnail = (preset: LoadedPreset): string => {
    // Generar thumbnail basado en categoría/tipo
    const thumbnails: Record<string, string> = {
      'neural_network': '🧠',
      'abstract-lines': '📈',
      'abstract-shapes': '🔷',
      'evolutive-particles': '✨',
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
                  <div className="preset-thumbnail">
                    {getPresetThumbnail(preset)}
                  </div>
                  <div className="preset-info">
                    <div className="preset-name">{preset.config.name}</div>
                    <div className="preset-category">{preset.config.category}</div>
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
