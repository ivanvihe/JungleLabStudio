import React, { useState } from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { PresetControls } from './PresetControls';
import { setNestedValue } from '../utils/objectPath';
import './PresetGalleryModal.css';

interface PresetGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  presets: LoadedPreset[];
  onCustomTextCountChange?: (count: number) => void;
  currentCustomTextCount?: number;
}

export const PresetGalleryModal: React.FC<PresetGalleryModalProps> = ({
  isOpen,
  onClose,
  presets,
  onCustomTextCountChange,
  currentCustomTextCount = 1
}) => {
  const [selected, setSelected] = useState<LoadedPreset | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [customTextCount, setCustomTextCount] = useState(currentCustomTextCount);

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
  const getFilteredPresets = () => {
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

  if (!isOpen) return null;

  return (
    <div className={`preset-gallery-overlay ${isDragging ? 'dragging' : ''}`} onClick={onClose}>
      <div className="preset-gallery-modal" onClick={e => e.stopPropagation()}>
        
        {/* Header con configuraciones */}
        <div className="preset-gallery-header">
          <h2>🎨 Presets Gallery</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="preset-gallery-content">
          {/* Grid de presets */}
          <div className="preset-gallery-grid">
            {getFilteredPresets().map(preset => (
              <div
                key={preset.id}
                className="preset-gallery-item preset-cell"
                onClick={() => setSelected(preset)}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('text/plain', preset.id);
                  setIsDragging(true);
                  document.body.classList.add('preset-dragging');
                }}
                onDragEnd={() => {
                  setIsDragging(false);
                  document.body.classList.remove('preset-dragging');
                }}
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
            ))}
          </div>

          {/* Panel de controles */}
          <div className="preset-gallery-controls">
            {selected ? (
              <div className="controls-panel">
                <div className="controls-header">
                  <h3>{selected.config.name}</h3>
                  <span className="preset-category-badge">{selected.config.category}</span>
                </div>
                
                {/* Configuración especial para Custom Text */}
                {isCustomTextPreset(selected) && (
                  <div className="custom-text-config">
                    <div className="config-section">
                      <label>Cantidad de instancias de Custom Text:</label>
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
                    <div className="config-description">
                      Se crearán {customTextCount} instancia{customTextCount > 1 ? 's' : ''} de Custom Text, 
                      cada una con su propio texto configurable.
                    </div>
                  </div>
                )}

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
                    <div>• <strong>Drag & Drop:</strong> Arrastrar al grid principal</div>
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