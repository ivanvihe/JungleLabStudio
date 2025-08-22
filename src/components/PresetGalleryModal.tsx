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

  if (!isOpen) return null;

  return (
    <div className="preset-gallery-overlay" onClick={onClose}>
      <div className="preset-gallery-modal" onClick={e => e.stopPropagation()}>
        <div className="preset-gallery-grid">
          {presets.map(preset => (
            <div
              key={preset.id}
              className="preset-gallery-item"
              onClick={() => setSelected(preset)}
              draggable
              onDragStart={(e) => e.dataTransfer.setData('text/plain', preset.id)}
            >
              <div className="preset-gallery-thumb">{preset.config.thumbnail || '🎨'}</div>
              <div className="preset-gallery-name">{preset.config.name}</div>
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
