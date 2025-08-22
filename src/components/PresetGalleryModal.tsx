import React, { useState } from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { PresetControls } from './PresetControls';
import { setNestedValue } from '../utils/objectPath';
import './PresetGalleryModal.css';

interface PresetGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  presets: LoadedPreset[];
}

export const PresetGalleryModal: React.FC<PresetGalleryModalProps> = ({
  isOpen,
  onClose,
  presets
}) => {
  const [selected, setSelected] = useState<LoadedPreset | null>(null);
  const [isDragging, setIsDragging] = useState(false);

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
      'text-glitch': '🔤'
    };
    return thumbnails[preset.id] || '🎨';
  };

  if (!isOpen) return null;

  return (
    <div className={`preset-gallery-overlay ${isDragging ? 'dragging' : ''}`} onClick={onClose}>
      <div className="preset-gallery-modal" onClick={e => e.stopPropagation()}>
        <div className="preset-gallery-grid">
          {presets.map(preset => (
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
        <div className="preset-gallery-controls">
          {selected ? (
            <PresetControls
              preset={selected}
              config={selected.config.defaultConfig}
              onConfigUpdate={(path, value) => {
                const cfg = { ...selected.config.defaultConfig };
                setNestedValue(cfg, path, value);
                selected.config.defaultConfig = cfg;
              }}
            />
          ) : (
            <div className="preset-gallery-placeholder">
              Selecciona un visual para editar sus valores por defecto
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
