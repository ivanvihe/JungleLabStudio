import React from 'react';
import { LoadedPreset } from '../core/PresetLoader';

interface PresetControlsProps {
  preset: LoadedPreset;
  onConfigUpdate: (config: any) => void;
}

export const PresetControls: React.FC<PresetControlsProps> = ({ preset, onConfigUpdate }) => {
  const handleControlChange = (controlName: string, value: any, type: string) => {
    let processedValue = value;
    if (type === 'slider' || type === 'number') {
      processedValue = parseFloat(value);
    } else if (type === 'checkbox') {
      processedValue = value;
    }
    const config = createNestedConfig(controlName, processedValue);
    onConfigUpdate(config);
  };

  const createNestedConfig = (path: string, value: any): any => {
    const keys = path.split('.');
    const config: any = {};
    let current = config;
    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = {};
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
    return config;
  };

  const renderControl = (control: any) => {
    switch (control.type) {
      case 'slider':
        return (
          <input
            type="range"
            min={control.min || 0}
            max={control.max || 1}
            step={control.step || 0.01}
            defaultValue={control.default || 0}
            onChange={(e) => handleControlChange(control.name, e.target.value, 'slider')}
            className="control-slider"
          />
        );
      case 'number':
        return (
          <input
            type="number"
            min={control.min}
            max={control.max}
            step={control.step || 1}
            defaultValue={control.default || 0}
            onChange={(e) => handleControlChange(control.name, e.target.value, 'number')}
            className="control-text"
          />
        );
      case 'color':
        return (
          <input
            type="color"
            defaultValue={control.default || '#ffffff'}
            onChange={(e) => handleControlChange(control.name, e.target.value, 'color')}
            className="control-color"
          />
        );
      case 'checkbox':
        return (
          <input
            type="checkbox"
            defaultChecked={control.default || false}
            onChange={(e) => handleControlChange(control.name, e.target.checked, 'checkbox')}
            className="control-checkbox"
          />
        );
      case 'select':
        return (
          <select
            defaultValue={control.default || ''}
            onChange={(e) => handleControlChange(control.name, e.target.value, 'select')}
            className="control-select"
          >
            {control.options?.map((option: string) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      default:
        return (
          <input
            type="text"
            defaultValue={control.default?.toString() || ''}
            onChange={(e) => handleControlChange(control.name, e.target.value, 'text')}
            className="control-text"
          />
        );
    }
  };

  const basicControls = [
    { name: 'width', type: 'number', label: 'Width', min: 0, max: 4096, default: preset.config.defaultConfig.width || 1920 },
    { name: 'height', type: 'number', label: 'Height', min: 0, max: 4096, default: preset.config.defaultConfig.height || 1080 },
    { name: 'zoom', type: 'slider', label: 'Zoom', min: 0.1, max: 5, step: 0.1, default: preset.config.defaultConfig.zoom || 1 },
  ];

  const audioControls = [
    { name: 'audioSensitivity', type: 'slider', label: 'Sensitivity', min: 0, max: 2, step: 0.01, default: preset.config.defaultConfig.audioSensitivity || 1 },
    { name: 'audioSmoothness', type: 'slider', label: 'Smoothness', min: 0, max: 1, step: 0.01, default: preset.config.defaultConfig.audioSmoothness || 0.5 },
    { name: 'audioReactivity', type: 'slider', label: 'Reactivity', min: 0, max: 2, step: 0.01, default: preset.config.defaultConfig.audioReactivity || 1 },
  ];

  return (
    <div className="preset-controls-container">
      <div className="preset-header">
        <h3>{preset.config.name}</h3>
        <div className="preset-meta-line">Versión: {preset.config.version}</div>
        <div className="preset-meta-line">Categoría: {preset.config.category}</div>
        <div className="preset-meta-line">Autor: {preset.config.author}</div>
        {preset.config.tags && (
          <>
            <div className="section-divider" />
            <div className="preset-tags-line">
              tags: {preset.config.tags.join(', ')}
            </div>
            <div className="section-divider" />
          </>
        )}
      </div>

      <div className="section">
        <h4 className="section-title">BASIC PARAMETERS</h4>
        <div className="control-group">
          <label className="control-label">Output area:</label>
          <div className="output-area-inputs">
            {renderControl(basicControls[0])}
            <span>/</span>
            {renderControl(basicControls[1])}
          </div>
        </div>
        <div className="control-group">
          <label className="control-label">{basicControls[2].label}</label>
          {renderControl(basicControls[2])}
        </div>
      </div>

      <div className="section">
        <h4 className="section-title">AUDIO</h4>
        {audioControls.map(control => (
          <div key={control.name} className="control-group">
            <label className="control-label">{control.label}</label>
            {renderControl(control)}
          </div>
        ))}
      </div>

      {preset.config.controls && preset.config.controls.length > 0 && (
        <div className="section">
          <div className="section-divider" />
          <h4 className="section-title">PRESET CONTROLS</h4>
          {preset.config.controls.map(control => (
            <div key={control.name} className="control-group">
              <label className="control-label">{control.label}</label>
              {renderControl(control)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
