import React from 'react';
import { LoadedPreset } from '../core/PresetLoader';

interface PresetControlsProps {
  preset: LoadedPreset;
  onConfigUpdate: (config: any) => void;
}

export const PresetControls: React.FC<PresetControlsProps> = ({
  preset,
  onConfigUpdate
}) => {
  const handleControlChange = (controlName: string, value: any, type: string) => {
    let processedValue = value;

    // Procesar valor según el tipo
    if (type === 'slider' || type === 'number') {
      processedValue = parseFloat(value);
    } else if (type === 'checkbox') {
      processedValue = value;
    }
    
    // Crear objeto de configuración usando el path del control
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

  const baseControls = [
    {
      name: 'width',
      type: 'number',
      label: 'Width',
      min: 0,
      max: 4096,
      default: preset.config.defaultConfig.width || 1920
    },
    {
      name: 'height',
      type: 'number',
      label: 'Height',
      min: 0,
      max: 4096,
      default: preset.config.defaultConfig.height || 1080
    },
    {
      name: 'zoom',
      type: 'slider',
      label: 'Zoom',
      min: 0.1,
      max: 5,
      step: 0.1,
      default: preset.config.defaultConfig.zoom || 1
    },
    {
      name: 'audioSensitivity',
      type: 'slider',
      label: 'Audio Sensitivity',
      min: 0,
      max: 2,
      step: 0.01,
      default: preset.config.defaultConfig.audioSensitivity || 1
    },
    {
      name: 'audioSmoothness',
      type: 'slider',
      label: 'Audio Smoothness',
      min: 0,
      max: 1,
      step: 0.01,
      default: preset.config.defaultConfig.audioSmoothness || 0.5
    },
    {
      name: 'audioReactivity',
      type: 'slider',
      label: 'Audio Reactivity',
      min: 0,
      max: 2,
      step: 0.01,
      default: preset.config.defaultConfig.audioReactivity || 1
    },
    {
      name: 'paletteColor',
      type: 'color',
      label: 'Palette Color',
      default: preset.config.defaultConfig.paletteColor || '#ffffff'
    }
  ];

  const combinedControls = [...baseControls, ...preset.config.controls];

  return (
    <div className="preset-controls-container">
      <div className="preset-info">
        <h3>{preset.config.name}</h3>
        <p>{preset.config.description}</p>
        <div className="preset-meta">
          <span>Autor: {preset.config.author}</span>
          <span>Versión: {preset.config.version}</span>
          <span>Categoría: {preset.config.category}</span>
        </div>
        
        {preset.config.tags && preset.config.tags.length > 0 && (
          <div className="preset-tags">
            {preset.config.tags.map(tag => (
              <span key={tag} className="tag">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="controls-list">
        <h4>Controles</h4>
        {combinedControls.map((control) => (
          <div key={control.name} className="control-group">
            <label className="control-label">
              {control.label}:
            </label>
            {renderControl(control)}
          </div>
        ))}
      </div>

      {preset.config.audioMapping && (
        <div className="audio-mapping">
          <h4>Mapeo de Audio</h4>
          <div className="mapping-item">
            <strong>Bajos ({preset.config.audioMapping.low.frequency}):</strong>
            <p>{preset.config.audioMapping.low.effect}</p>
          </div>
          <div className="mapping-item">
            <strong>Medios ({preset.config.audioMapping.mid.frequency}):</strong>
            <p>{preset.config.audioMapping.mid.effect}</p>
          </div>
          <div className="mapping-item">
            <strong>Agudos ({preset.config.audioMapping.high.frequency}):</strong>
            <p>{preset.config.audioMapping.high.effect}</p>
          </div>
        </div>
      )}

      {preset.config.performance && (
        <div className="performance-info">
          <h4>Información de Rendimiento</h4>
          <p>Complejidad: <span className={`complexity-${preset.config.performance.complexity}`}>
            {preset.config.performance.complexity}
          </span></p>
          <p>FPS Recomendado: {preset.config.performance.recommendedFPS}</p>
          <p>GPU Intensivo: {preset.config.performance.gpuIntensive ? 'Sí' : 'No'}</p>
        </div>
      )}
    </div>
  );
};