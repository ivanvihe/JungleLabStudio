import React, { useState, useEffect } from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { AVAILABLE_EFFECTS } from '../utils/effects';
import './LayerGrid.css';

interface LayerConfig {
  id: string;
  name: string;
  color: string;
  midiChannel: number;
  fadeTime: number;
  opacity: number;
  activePreset: string | null;
  autoJump: boolean;
  jumpDirection: 'right' | 'left' | 'random';
  jumpSync: 'time' | 'beats';
  /**
   * Jump interval in seconds when `jumpSync` is `time` or as a beat
   * fraction (e.g. "2/4") when `jumpSync` is `beats`.
   */
  jumpInterval: number | string;
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
  onOpenPresetGallery: () => void;
  layerEffects: Record<string, { effect: string; alwaysOn: boolean; active: boolean }>;
  onLayerEffectChange: (layerId: string, effect: string) => void;
  onLayerEffectToggle: (layerId: string, alwaysOn: boolean) => void;
  bpm: number | null;
}

export const LayerGrid: React.FC<LayerGridProps> = ({
  presets,
  onPresetActivate,
  onLayerClear,
  onLayerConfigChange,
  onPresetSelect,
  clearAllSignal,
  externalTrigger,
  layerChannels,
  onOpenPresetGallery,
  layerEffects,
  onLayerEffectChange,
  onLayerEffectToggle,
  bpm
}) => {
  const [layers, setLayers] = useState<LayerConfig[]>([
    { id: 'A', name: 'Layer A', color: '#FF6B6B', midiChannel: layerChannels.A || 14, fadeTime: 200, opacity: 100, activePreset: null, autoJump: false, jumpDirection: 'right', jumpSync: 'time', jumpInterval: 1 },
    { id: 'B', name: 'Layer B', color: '#4ECDC4', midiChannel: layerChannels.B || 15, fadeTime: 200, opacity: 100, activePreset: null, autoJump: false, jumpDirection: 'right', jumpSync: 'time', jumpInterval: 1 },
    { id: 'C', name: 'Layer C', color: '#45B7D1', midiChannel: layerChannels.C || 16, fadeTime: 200, opacity: 100, activePreset: null, autoJump: false, jumpDirection: 'right', jumpSync: 'time', jumpInterval: 1 },
  ]);

  useEffect(() => {
    setLayers(prev => prev.map(layer => ({ ...layer, activePreset: null })));
    setClickedCell(null);
  }, [clearAllSignal]);

  const [clickedCell, setClickedCell] = useState<string | null>(null);
  // Dynamic slots per layer based on available width
  const SLOT_WIDTH = 98; // width + gap per cell
  const SIDEBAR_WIDTH = 100; // sidebar with controls

  const calculateSlots = () => {
    const available = window.innerWidth - SIDEBAR_WIDTH - 40; // padding
    return Math.max(1, Math.floor(available / SLOT_WIDTH));
  };

  const initialSlots = calculateSlots();
  const [slotsPerLayer, setSlotsPerLayer] = useState(initialSlots);

  const defaultOrder = presets.map(p => p.id);
  const [layerPresets, setLayerPresets] = useState<Record<string, (string | null)[]>>(() => {
    try {
      const stored = localStorage.getItem('layerPresets');
      if (stored) {
        const parsed = JSON.parse(stored);
        const ensureSlots = (arr?: (string | null)[]) => {
          const result = Array.isArray(arr) ? [...arr] : [];
          // Ensure we have exactly `slotsPerLayer` slots
          while (result.length < slotsPerLayer) {
            result.push(null);
          }
          if (result.length > slotsPerLayer) {
            result.splice(slotsPerLayer);
          }
          return result;
        };
        return {
          A: ensureSlots(parsed.A),
          B: ensureSlots(parsed.B),
          C: ensureSlots(parsed.C)
        };
      }
    } catch {
      /* ignore */
    }
    // Inicializar con slots vacíos
    return {
      A: Array(slotsPerLayer).fill(null),
      B: Array(slotsPerLayer).fill(null),
      C: Array(slotsPerLayer).fill(null)
    };
  });

  const [dragTarget, setDragTarget] = useState<{ layerId: string; index: number } | null>(null);
  const jumpPositions = React.useRef<Record<string, number>>({});

  useEffect(() => {
    localStorage.setItem('layerPresets', JSON.stringify(layerPresets));
  }, [layerPresets]);

  useEffect(() => {
    const handleResize = () => {
      const slots = calculateSlots();
      setSlotsPerLayer(slots);
      setLayerPresets(prev => {
        const adjust = (arr: (string | null)[]) => {
          const res = [...arr];
          while (res.length < slots) res.push(null);
          if (res.length > slots) res.splice(slots);
          return res;
        };
        return {
          A: adjust(prev.A),
          B: adjust(prev.B),
          C: adjust(prev.C)
        };
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const getBaseId = (id: string) => (id.startsWith('custom-glitch-text') ? 'custom-glitch-text' : id);
  
  const canPlace = (list: (string | null)[], id: string, ignoreIndex?: number) => {
    const base = getBaseId(id);
    // Custom text puede tener múltiples instancias
    if (base === 'custom-glitch-text') return true;
    // Otros presets solo una instancia por layer
    return !list.some((pid, idx) => pid && getBaseId(pid) === base && idx !== ignoreIndex);
  };

  // Añadir un preset a una posición específica del layer
  const addPresetToLayer = (layerId: string, presetId: string) => {
    setLayerPresets(prev => {
      const next = { ...prev };
      const list = [...next[layerId]];
      
      // Buscar primer slot vacío
      const emptyIndex = list.findIndex(slot => slot === null);
      if (emptyIndex !== -1) {
        // Verificar si se puede colocar
        if (canPlace(list, presetId, emptyIndex)) {
          list[emptyIndex] = presetId;
          next[layerId] = list;
          return next;
        }
      }
      return prev;
    });
  };

  const removePresetFromLayer = (layerId: string, presetId: string) => {
    setLayerPresets(prev => {
      const next = { ...prev };
      const list = [...next[layerId]];
      const idx = list.findIndex(id => id === presetId);
      if (idx !== -1) {
        list[idx] = null;
        next[layerId] = list;
        return next;
      }
      return prev;
    });
  };

  // Exponer función para uso externo
  React.useEffect(() => {
    if (!(window as any).addPresetToLayer) {
      (window as any).addPresetToLayer = addPresetToLayer;
    }
    if (!(window as any).removePresetFromLayer) {
      (window as any).removePresetFromLayer = removePresetFromLayer;
    }
    return () => {
      delete (window as any).addPresetToLayer;
      delete (window as any).removePresetFromLayer;
    };
  }, []);

  const handleDragStart = (
    e: React.DragEvent<HTMLDivElement>,
    layerId: string,
    index: number
  ) => {
    const presetId = layerPresets[layerId][index];
    if (!presetId) return;
    
    e.dataTransfer.setData('application/json', JSON.stringify({ 
      layerId, 
      index,
      presetId,
      source: 'layer-grid'
    }));
    e.dataTransfer.effectAllowed = 'move';
    document.body.classList.add('preset-dragging');
  };

  const handleDragEnd = () => {
    document.body.classList.remove('preset-dragging');
    setDragTarget(null);
  };

  const handleDragEnter = (
    e: React.DragEvent<HTMLDivElement>,
    layerId: string,
    index: number
  ) => {
    e.preventDefault();
    setDragTarget({ layerId, index });
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    // Solo limpiar si realmente salimos del elemento
    const rect = e.currentTarget.getBoundingClientRect();
    const { clientX, clientY } = e;
    if (
      clientX < rect.left ||
      clientX > rect.right ||
      clientY < rect.top ||
      clientY > rect.bottom
    ) {
      setDragTarget(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (
    e: React.DragEvent<HTMLDivElement>,
    targetLayerId: string,
    targetIndex: number
  ) => {
    e.preventDefault();
    setDragTarget(null);
    
    const jsonData = e.dataTransfer.getData('application/json');
    const plainData = e.dataTransfer.getData('text/plain');

    // Drop desde preset gallery (usando text/plain)
    if (plainData && !jsonData) {
      setLayerPresets(prev => {
        const next = { ...prev };
        const list = [...next[targetLayerId]];
        if (!canPlace(list, plainData, targetIndex)) return prev;
        list[targetIndex] = plainData;
        next[targetLayerId] = list;
        return next;
      });
      document.body.classList.remove('preset-dragging');
      return;
    }

    // Drop interno (mover dentro del grid)
    if (!jsonData) return;
    
    try {
      const dragData = JSON.parse(jsonData);
      const { layerId: sourceLayerId, index: sourceIndex, source } = dragData;
      
      if (source !== 'layer-grid' || sourceLayerId === undefined || sourceIndex === undefined) return;

      setLayerPresets(prev => {
        const next = { ...prev };
        
        if (sourceLayerId === targetLayerId) {
          // Mover dentro de la misma layer
          const list = [...next[sourceLayerId]];
          const [item] = list.splice(sourceIndex, 1);
          list.splice(targetIndex, 0, item);
          
          // Rellenar con nulls si es necesario segun slotsPerLayer
          while (list.length < slotsPerLayer) {
            list.push(null);
          }
          if (list.length > slotsPerLayer) {
            list.splice(slotsPerLayer);
          }
          
          next[sourceLayerId] = list;
          return next;
        }
        
        // Mover entre layers diferentes (intercambio)
        const sourceList = [...next[sourceLayerId]];
        const targetList = [...next[targetLayerId]];
        const draggedId = sourceList[sourceIndex];
        const targetId = targetList[targetIndex];
        
        if (draggedId && !canPlace(targetList, draggedId, targetIndex)) {
          return prev;
        }
        if (targetId && !canPlace(sourceList, targetId, sourceIndex)) {
          return prev;
        }
        
        sourceList[sourceIndex] = targetId;
        targetList[targetIndex] = draggedId;
        next[sourceLayerId] = sourceList;
        next[targetLayerId] = targetList;
        return next;
      });
    } catch (error) {
      console.error('Error en drop:', error);
    }
    
    document.body.classList.remove('preset-dragging');
  };

  const handlePresetClick = (layerId: string, presetId: string, velocity?: number) => {
    if (!presetId) return; // No hacer nada si es un slot vacío
    
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
    onPresetSelect(layerId, '');
  };

  const handleLayerConfigChange = (layerId: string, field: keyof LayerConfig, value: any) => {
    setLayers(prev => prev.map(layer =>
      layer.id === layerId
        ? { ...layer, [field]: value }
        : layer
    ));

    if (['midiChannel', 'fadeTime', 'opacity'].includes(field)) {
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

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    layers.forEach(layer => {
      if (!layer.autoJump) return;
      const list = layerPresets[layer.id];
      if (!list.some(p => p)) return;

      let intervalMs: number | null = null;
      if (layer.jumpSync === 'time') {
        const val = typeof layer.jumpInterval === 'number'
          ? layer.jumpInterval
          : parseFloat(layer.jumpInterval as string) || 0;
        intervalMs = val * 1000;
      } else if (layer.jumpSync === 'beats' && bpm) {
        let ratio = 1;
        if (typeof layer.jumpInterval === 'string') {
          const parts = layer.jumpInterval.split('/').map(n => parseFloat(n));
          if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1]) && parts[1] !== 0) {
            ratio = parts[0] / parts[1];
          }
        } else if (typeof layer.jumpInterval === 'number') {
          ratio = layer.jumpInterval;
        }
        intervalMs = (60 / bpm) * ratio * 1000;
      }

      if (!intervalMs) return;

      const timer = setInterval(() => {
        const currentList = layerPresets[layer.id];
        const valid = currentList.map((p, idx) => ({ p, idx })).filter(v => v.p);
        if (valid.length === 0) return;
        let idx: number;
        if (layer.jumpDirection === 'random') {
          idx = valid[Math.floor(Math.random() * valid.length)].idx;
        } else {
          let cur = jumpPositions.current[layer.id] ?? (layer.jumpDirection === 'right' ? -1 : valid.length);
          const step = layer.jumpDirection === 'right' ? 1 : -1;
          do {
            cur = (cur + step + currentList.length) % currentList.length;
          } while (!currentList[cur]);
          jumpPositions.current[layer.id] = cur;
          idx = cur;
        }
        const presetId = currentList[idx];
        if (presetId) {
          handlePresetClick(layer.id, presetId);
        }
      }, intervalMs);

      timers.push(timer);
    });

    return () => {
      timers.forEach(clearInterval);
    };
  }, [layers, layerPresets, bpm]);

  const getPresetThumbnail = (preset: LoadedPreset): string => {
    const thumbnails: Record<string, string> = {
      'neural_network': '🧠',
      'abstract-lines': '📈',
      'abstract-lines-pro': '📊',
      'abstract-shapes': '🔷',
      'evolutive-particles': '✨',
      'boom-wave': '💥',
      'plasma-ray': '⚡',
      'shot-text': '📝',
      'text-glitch': '🔤',
      'custom-glitch-text': '📝'
    };
    return thumbnails[preset.id] || thumbnails[preset.id.split('-')[0]] || '🎨';
  };

  return (
    <div className="layer-grid">
      {layers.map((layer) => {
        return (
        <div key={layer.id} className="layer-section">
          <div className={`layer-header ${layerEffects[layer.id]?.active ? 'effect-active' : ''}`}>
            <div className="midi-channel-edit">
              <label>MIDI</label>
              <input
                type="number"
                min={1}
                max={16}
                value={layer.midiChannel}
                onChange={(e) =>
                  handleLayerConfigChange(layer.id, 'midiChannel', parseInt(e.target.value))
                }
                className="midi-channel-input"
              />
            </div>
            <span className="control-separator">|</span>
            <select
              value={layerEffects[layer.id]?.effect}
              onChange={(e) => onLayerEffectChange(layer.id, e.target.value)}
            >
              {AVAILABLE_EFFECTS.map((eff) => (
                <option key={eff} value={eff}>
                  {eff}
                </option>
              ))}
            </select>
            <label className="effect-always">
              <input
                type="checkbox"
                checked={layerEffects[layer.id]?.alwaysOn}
                onChange={(e) => onLayerEffectToggle(layer.id, e.target.checked)}
              />
              Always
            </label>
            <span className="control-separator">|</span>
            <div className="jump-controls">
              <label>
                <input
                  type="checkbox"
                  checked={layer.autoJump}
                  onChange={(e) => handleLayerConfigChange(layer.id, 'autoJump', e.target.checked)}
                />
                Jump
              </label>
              <select
                value={layer.jumpDirection}
                onChange={(e) =>
                  handleLayerConfigChange(layer.id, 'jumpDirection', e.target.value as any)
                }
              >
                <option value="right">right</option>
                <option value="left">left</option>
                <option value="random">random</option>
              </select>
              <select
                value={layer.jumpSync}
                onChange={(e) => {
                  const val = e.target.value as any;
                  handleLayerConfigChange(layer.id, 'jumpSync', val);
                  if (val === 'time' && typeof layer.jumpInterval === 'string') {
                    const parts = layer.jumpInterval.split('/').map(n => parseFloat(n));
                    const num = parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1]) && parts[1] !== 0 ? parts[0] / parts[1] : 1;
                    handleLayerConfigChange(layer.id, 'jumpInterval', num);
                  }
                  if (val === 'beats' && typeof layer.jumpInterval === 'number') {
                    handleLayerConfigChange(layer.id, 'jumpInterval', '4/4');
                  }
                }}
              >
                <option value="time">time</option>
                <option value="beats">beats</option>
              </select>
              {layer.jumpSync === 'time' ? (
                <input
                  type="number"
                  min={1}
                  value={layer.jumpInterval as number}
                  onChange={(e) =>
                    handleLayerConfigChange(layer.id, 'jumpInterval', parseInt(e.target.value))
                  }
                  className="jump-interval-input"
                />
              ) : (
                <input
                  type="text"
                  value={layer.jumpInterval as string}
                  onChange={(e) =>
                    handleLayerConfigChange(layer.id, 'jumpInterval', e.target.value)
                  }
                  className="jump-interval-input"
                  placeholder="4/4"
                  pattern="\d+/\d+"
                />
              )}
            </div>
          </div>

          {/* Layer Controls - 100x100 square */}
          <div className="layer-content">
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

            {/* Preset Grid con slots fijos */}
            <div className="preset-grid">
              {layerPresets[layer.id].map((presetId, idx) => {
              // Slot vacío
              if (!presetId) {
                const isDragOver = dragTarget?.layerId === layer.id && dragTarget.index === idx;
                return (
                  <div
                    key={`${layer.id}-empty-${idx}`}
                    className={`preset-cell empty-slot ${isDragOver ? 'drag-over' : ''}`}
                    onClick={onOpenPresetGallery}
                    onDragOver={handleDragOver}
                    onDragEnter={(e) => handleDragEnter(e, layer.id, idx)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, layer.id, idx)}
                    style={{
                      '--layer-color': layer.color,
                      '--layer-color-alpha': layer.color + '20'
                    } as React.CSSProperties}
                  >
                    <div className="empty-slot-indicator">
                      <div className="empty-slot-icon">+</div>
                    </div>
                  </div>
                );
              }

              // Slot con preset
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
                  onDragEnd={handleDragEnd}
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
        </div>
        );
      })}
    </div>
  );
};
