import React from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { getNestedValue, setNestedValue } from '../utils/objectPath';
import './PresetControls.css';

interface PresetControlsProps {
  preset: LoadedPreset;
  config: Record<string, any>;
  onChange?: (path: string, value: any) => void;
  isReadOnly?: boolean;
}

export const PresetControls: React.FC<PresetControlsProps> = ({
  preset,
  config,
  onChange,
  isReadOnly = false
}) => {
  const handleControlChange = (controlName: string, value: any) => {
    if (isReadOnly || !onChange) return;
    onChange(controlName, value);
  };

  const getControlValue = (controlName: string, defaultValue: any): any => {
    if (config) {
      const value = getNestedValue(config, controlName);
      return value !== undefined ? value : defaultValue;
    }
    return defaultValue;
  };

  const isCustomTextPreset = preset.id.startsWith('custom-glitch-text');

  const renderControl = (control: any) => {
    const value = getControlValue(control.name, control.default);
    const controlId = `${preset.id}-${control.name}`;

    switch (control.type) {
      case 'slider':
        return (
          <div key={control.name} className="control-group">
            <label htmlFor={controlId} className="control-label">
              {control.label}
              {isCustomTextPreset && control.name === 'text.content' && (
                <span className="custom-text-indicator">✨</span>
              )}
            </label>
            <div className="slider-container">
              <input
                id={controlId}
                type="range"
                min={control.min}
                max={control.max}
                step={control.step}
                value={value}
                onChange={(e) => handleControlChange(control.name, parseFloat(e.target.value))}
                className="control-slider"
                disabled={isReadOnly}
              />
              <input
                type="number"
                min={control.min}
                max={control.max}
                step={control.step}
                value={value}
                onChange={(e) => handleControlChange(control.name, parseFloat(e.target.value))}
                className="slider-number"
                disabled={isReadOnly}
              />
            </div>
          </div>
        );

      case 'text':
        return (
          <div key={control.name} className="control-group">
            <label htmlFor={controlId} className="control-label">
              {control.label}
              {isCustomTextPreset && control.name === 'text.content' && (
                <span className="custom-text-indicator">✨</span>
              )}
            </label>
            <div className="text-control-container">
              <input
                id={controlId}
                type="text"
                value={value || ''}
                onChange={(e) => handleControlChange(control.name, e.target.value)}
                className={`control-text ${isCustomTextPreset ? 'custom-text-input' : ''}`}
                placeholder={control.placeholder || control.label}
                disabled={isReadOnly}
              />
              {isCustomTextPreset && control.name === 'text.content' && !isReadOnly && (
                <div className="text-control-hints">
                  <small>Texto personalizado para esta instancia</small>
                </div>
              )}
            </div>
          </div>
        );

      case 'color':
        return (
          <div key={control.name} className="control-group">
            <label htmlFor={controlId} className="control-label">
              {control.label}
            </label>
            <div className="color-control-container">
              <input
                id={controlId}
                type="color"
                value={value || control.default}
                onChange={(e) => handleControlChange(control.name, e.target.value)}
                className="control-color"
                disabled={isReadOnly}
              />
              <input
                type="text"
                value={value || control.default}
                onChange={(e) => handleControlChange(control.name, e.target.value)}
                className="control-color-text"
                placeholder="#ffffff"
                disabled={isReadOnly}
              />
            </div>
          </div>
        );

      case 'checkbox':
        return (
          <div key={control.name} className="control-group">
            <label htmlFor={controlId} className="control-checkbox-label">
              <input
                id={controlId}
                type="checkbox"
                checked={!!value}
                onChange={(e) => handleControlChange(control.name, e.target.checked)}
                className="control-checkbox"
                disabled={isReadOnly}
              />
              <span className="checkbox-custom"></span>
              {control.label}
            </label>
          </div>
        );

      case 'select':
        return (
          <div key={control.name} className="control-group">
            <label htmlFor={controlId} className="control-label">
              {control.label}
            </label>
            <select
              id={controlId}
              value={value || control.default}
              onChange={(e) => handleControlChange(control.name, e.target.value)}
              className="control-select"
              disabled={isReadOnly}
            >
              {control.options?.map((option: string) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        );

      default:
        return null;
    }
  };

  if (!preset.config.controls || preset.config.controls.length === 0) {
    return (
      <div className="preset-controls no-controls">
        <p>No hay controles disponibles para este preset.</p>
      </div>
    );
  }

  return (
    <div className={`preset-controls ${isCustomTextPreset ? 'custom-text-controls' : ''} ${isReadOnly ? 'read-only' : ''}`}>
      {isCustomTextPreset && !isReadOnly && (
        <div className="custom-text-header">
          <div className="custom-text-badge">
            📝 Custom Text Instance
          </div>
          <div className="instance-info">
            <small>Instancia: {preset.config.name}</small>
          </div>
        </div>
      )}

      <div className="controls-container">
        {preset.config.controls.map(renderControl)}
      </div>

      {preset.config.audioMapping && (
        <div className="audio-mapping">
          <h4>Mapeo de Audio</h4>
          <div className="audio-mapping-grid">
            {Object.entries(preset.config.audioMapping).map(([band, mapping]: [string, any]) => (
              <div key={band} className="audio-band">
                <div className="band-label">{band.toUpperCase()}</div>
                <div className="band-frequency">{mapping.frequency}</div>
                <div className="band-effect">{mapping.effect}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {isReadOnly && (
        <div className="read-only-notice">
          <small>👁️ Vista previa - Los valores se aplicarán al añadir a una layer</small>
        </div>
      )}
    </div>
  );
};