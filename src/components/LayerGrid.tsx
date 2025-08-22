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
  onPresetActivate: (layerId: string, presetId: string, velocity?: number) => void;
  onLayerClear: (layerId: string) => void;
  onLayerConfigChange: (layerId: string, config: Partial<LayerConfig>) => void;
  onPresetSelect: (layerId: string, presetId: string) => void;
  clearAllSignal: number;
  externalTrigger?: { layerId: string; presetId: string; velocity: number } | null;
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

  const defaultOrder = presets.map(p => p.id);
  const [layerPresets, setLayerPresets] = useState<Record<string, string[]>>(() => {
    try {
      const stored = localStorage.getItem('layerPresets');
      if (stored) {
        const parsed = JSON.parse(stored);
        const ensure = (arr?: string[]) => {
          const result = Array.isArray(arr) ? [...arr] : [...defaultOrder];
          defaultOrder.forEach(id => {
            if (!result.includes(id)) result.push(id);
          });
          return result;
        };
        return {
          A: ensure(parsed.A),
          B: ensure(parsed.B),
          C: ensure(parsed.C)
        };
      }
    } catch {
      /* ignore */
    }
    return {
      A: [...defaultOrder],
      B: [...defaultOrder],
      C: [...defaultOrder]
    };
  });

  const [dragTarget, setDragTarget] = useState<{ layerId: string; index: number } | null>(null);

  useEffect(() => {
    localStorage.setItem('layerPresets', JSON.stringify(layerPresets));
  }, [layerPresets]);

  const getBaseId = (id: string) => (id.startsWith('custom-glitch-text') ? 'custom-glitch-text' : id);
  const canPlace = (list: string[], id: string, ignoreIndex?: number) => {
    const base = getBaseId(id);
    if (base === 'custom-glitch-text') return true;
    return !list.some((pid, idx) => getBaseId(pid) === base && idx !== ignoreIndex);
  };

  const handleDragStart = (
    e: React.DragEvent<HTMLDivElement>,
    layerId: string,
    index: number
  ) => {
    e.dataTransfer.setData('application/json', JSON.stringify({ layerId, index }));
  };

  const handleDragEnter = (
    e: React.DragEvent<HTMLDivElement>,
    layerId: string,
    index: number
  ) => {
    e.preventDefault();
    setDragTarget({ layerId, index });
  };

  const handleDragLeave = () => setDragTarget(null);
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => e.preventDefault();

  const handleDrop = (
    e: React.DragEvent<HTMLDivElement>,
    targetLayerId: string,
    targetIndex: number
  ) => {
    e.preventDefault();
    setDragTarget(null);
    const data = e.dataTransfer.getData('application/json');
    if (!data) return;
    const { layerId: sourceLayerId, index: sourceIndex } = JSON.parse(data);
    if (sourceLayerId === undefined) return;

    setLayerPresets(prev => {
      const next = { ...prev };
      if (sourceLayerId === targetLayerId) {
        const list = [...next[sourceLayerId]];
        const [item] = list.splice(sourceIndex, 1);
        list.splice(targetIndex, 0, item);
        next[sourceLayerId] = list;
        return next;
      }
      const sourceList = [...next[sourceLayerId]];
      const targetList = [...next[targetLayerId]];
      const draggedId = sourceList[sourceIndex];
      const targetId = targetList[targetIndex];
      if (
        !canPlace(targetList, draggedId, targetIndex) ||
        !canPlace(sourceList, targetId, sourceIndex)
      ) {
        return prev;
      }
      sourceList[sourceIndex] = targetId;
      targetList[targetIndex] = draggedId;
      next[sourceLayerId] = sourceList;
      next[targetLayerId] = targetList;
      return next;
    });
  };

  const handlePresetClick = (layerId: string, presetId: string, velocity?: number) => {
    const cellKey = `${layerId}-${presetId}`;
    const layer = layers.find(l => l.id === layerId);
    const wasActive = layer?.activePreset === presetId;
    const preset = presets.find(p => p.id === presetId);
    const isOneShot = preset?.config.category === 'one-shot';
    const opacityFromVelocity = velocity !== undefined
      ? Math.max(1, Math.round((velocity / 127) * 100))
      : undefined;

    setClickedCell(cellKey);
    setTimeout(() => setClickedCell(null), 150);

    setLayers(prev => prev.map(l =>
      l.id === layerId
        ? { ...l, activePreset: presetId, ...(opacityFromVelocity !== undefined ? { opacity: opacityFromVelocity } : {}) }
        : l
    ));

    if (opacityFromVelocity !== undefined) {
      onLayerConfigChange(layerId, { opacity: opacityFromVelocity });
    }

    if (!wasActive || isOneShot) {
      onPresetActivate(layerId, presetId, velocity);
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
      handlePresetClick(
        externalTrigger.layerId,
        externalTrigger.presetId,
        externalTrigger.velocity
      );
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
            {layerPresets[layer.id].map((presetId, idx) => {
              const preset = presets.find(p => p.id === presetId);
              if (!preset) return null;
              const cellKey = `${layer.id}-${preset.id}`;
              const isActive = layer.activePreset === preset.id;
              const isClicked = clickedCell === cellKey;
              const isDragOver = dragTarget?.layerId === layer.id && dragTarget.index === idx;

              return (
                <div
                  key={cellKey}
                  className={`preset-cell ${isActive ? 'active' : ''} ${isClicked ? 'clicked' : ''} ${isDragOver ? 'drag-over' : ''}`}
                  onClick={() => handlePresetClick(layer.id, preset.id)}
                  draggable
                  onDragStart={(e) => handleDragStart(e, layer.id, idx)}
                  onDragOver={handleDragOver}
                  onDragEnter={(e) => handleDragEnter(e, layer.id, idx)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, layer.id, idx)}
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
