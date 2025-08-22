import React, { useState } from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { PresetControls } from './PresetControls';
import './PresetGalleryModal.css';

interface PresetGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  presets: LoadedPreset[];
  onCustomTextCountChange?: (count: number) => void;
  currentCustomTextCount?: number;
  onAddPresetToLayer?: (presetId: string, layerId: string) => void;
  onRemovePresetFromLayer?: (presetId: string, layerId: string) => void;
}

export const PresetGalleryModal: React.FC<PresetGalleryModalProps> = ({
  isOpen,
  onClose,
  presets,
  onCustomTextCountChange,
  currentCustomTextCount = 1,
  onAddPresetToLayer,
  onRemovePresetFromLayer
}) => {
  const [selected, setSelected] = useState<LoadedPreset | null>(null);
  const [customTextCount, setCustomTextCount] = useState(currentCustomTextCount);
  const [layerAssignments, setLayerAssignments] = useState<Record<string, Set<string>>>(() => ({
    A: new Set(),
    B: new Set(),
    C: new Set()
  }));

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

  const handleCustomTextCountChange = (count: number) => {
    setCustomTextCount(count);
    if (onCustomTextCountChange) {
      onCustomTextCountChange(count);
    }
  };

  const isCustomTextPreset = (preset: LoadedPreset) => {
    return preset.id.startsWith('custom-glitch-text');
  };

  const getBasePresetId = (preset: LoadedPreset) => {
    return preset.id.split('-')[0] + '-' + preset.id.split('-')[1];
  };

  // Filtrar presets para mostrar solo uno de cada tipo (excepto custom text)
  const getMainPresets = () => {
    const seen = new Set<string>();
    return presets.filter(preset => {
      if (isCustomTextPreset(preset)) {
        const baseId = getBasePresetId(preset);
        if (seen.has(baseId)) return false;
        seen.add(baseId);
        return true;
      }
      return true;
    });
  };

  // Obtener instancias de custom text
  const getCustomTextInstances = () => {
    return presets.filter(preset => isCustomTextPreset(preset));
  };

  // Cargar asignaciones actuales desde localStorage al abrir el modal
  React.useEffect(() => {
    if (isOpen) {
      try {
        const stored = localStorage.getItem('layerPresets');
        if (stored) {
          const parsed = JSON.parse(stored);
          setLayerAssignments({
            A: new Set((parsed.A || []).filter((p: string | null) => p)),
            B: new Set((parsed.B || []).filter((p: string | null) => p)),
            C: new Set((parsed.C || []).filter((p: string | null) => p))
          });
        }
      } catch {
        /* ignore */
      }
    }
  }, [isOpen]);

  const toggleLayer = (presetId: string, layerId: string) => {
    setLayerAssignments(prev => {
      const set = new Set(prev[layerId]);
      if (set.has(presetId)) {
        if (onRemovePresetFromLayer) {
          onRemovePresetFromLayer(presetId, layerId);
        }
        set.delete(presetId);
      } else {
        if (onAddPresetToLayer) {
          onAddPresetToLayer(presetId, layerId);
        }
        set.add(presetId);
      }
      return { ...prev, [layerId]: set };
    });
  };

  if (!isOpen) return null;

  const mainPresets = getMainPresets();
  const customTextInstances = getCustomTextInstances();

  return (
    <div className="preset-gallery-overlay" onClick={onClose}>
      <div className="preset-gallery-modal" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="preset-gallery-header">
          <h2>🎨 Presets Gallery</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="preset-gallery-content">
          {/* Grid principal de presets */}
          <div className="preset-gallery-section">
            <h3>Presets Principales</h3>
            <div className="preset-gallery-grid">
              {mainPresets.map(preset => (
                <div key={preset.id} className="preset-gallery-item-wrapper">
                  <div
                    className="preset-gallery-item preset-cell"
                    onClick={() => setSelected(preset)}
                  >
                    {preset.config.note !== undefined && (
                      <div className="preset-note-badge">{preset.config.note}</div>
                    )}
                    <div className="preset-thumbnail">{getPresetThumbnail(preset)}</div>
                    <div className="preset-info">
                      <div className="preset-name">{preset.config.name}</div>
                      <div className="preset-details">
                        <span className="preset-category">{preset.config.category}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Botones de capas */}
                  <div className="layer-button-group">
                    {['A', 'B', 'C'].map(layer => (
                      <button
                        key={layer}
                        className={`layer-button ${layerAssignments[layer].has(preset.id) ? 'active' : ''}`}
                        onClick={e => {
                          e.stopPropagation();
                          toggleLayer(preset.id, layer);
                        }}
                      >
                        {layer}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Grid de instancias de Custom Text */}
          {customTextInstances.length > 0 && (
            <div className="preset-gallery-section">
              <div className="custom-text-header">
                <h3>Custom Text Instances</h3>
                <div className="custom-text-config">
                  <label>Cantidad:</label>
                  <div className="count-controls">
                    <button 
                      onClick={() => handleCustomTextCountChange(Math.max(1, customTextCount - 1))}
                      disabled={customTextCount <= 1}
                    >
                      -
                    </button>
                    <span className="count-display">{customTextCount}</span>
                    <button 
                      onClick={() => handleCustomTextCountChange(Math.min(10, customTextCount + 1))}
                      disabled={customTextCount >= 10}
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="preset-gallery-grid custom-text-grid">
                {customTextInstances.map(preset => (
                  <div key={preset.id} className="preset-gallery-item-wrapper">
                    <div
                      className="preset-gallery-item preset-cell custom-text-cell"
                      onClick={() => setSelected(preset)}
                    >
                      {preset.config.note !== undefined && (
                        <div className="preset-note-badge">{preset.config.note}</div>
                      )}
                      <div className="preset-thumbnail">{getPresetThumbnail(preset)}</div>
                      <div className="preset-info">
                        <div className="preset-name">{preset.config.name}</div>
                        <div className="preset-details">
                          <span className="preset-category">{preset.config.category}</span>
                        </div>
                      </div>
                      <div className="custom-text-preview">
                        {preset.config.defaultConfig?.text?.content || 'TEXT'}
                      </div>
                    </div>
                    
                    {/* Botones de capas */}
                    <div className="layer-button-group">
                      {['A', 'B', 'C'].map(layer => (
                        <button
                          key={layer}
                          className={`layer-button ${layerAssignments[layer].has(preset.id) ? 'active' : ''}`}
                          onClick={e => {
                            e.stopPropagation();
                            toggleLayer(preset.id, layer);
                          }}
                        >
                          {layer}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Panel de controles */}
          <div className="preset-gallery-controls">
            {selected ? (
              <div className="controls-panel">
                <div className="controls-header">
                  <h3>{selected.config.name}</h3>
                  <span className="preset-category-badge">{selected.config.category}</span>
                </div>
                
                {/* Controles por defecto del preset */}
                <div className="default-controls">
                  <h4>Valores por defecto:</h4>
                  <PresetControls
                    preset={selected}
                    config={selected.config.defaultConfig || {}}
                    onChange={() => {}} // Solo lectura para mostrar valores por defecto
                    isReadOnly={true}
                  />
                </div>
              </div>
            ) : (
              <div className="preset-gallery-placeholder">
                <div className="placeholder-content">
                  <div className="placeholder-icon">🎯</div>
                  <h3>Selecciona un preset</h3>
                  <p>Haz click en un preset para ver sus controles y valores por defecto</p>
                  <div className="placeholder-instructions">
                    <div>• <strong>Click:</strong> Ver controles y configuración</div>
                    <div>• <strong>A/B/C:</strong> Añadir o quitar de una layer</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};