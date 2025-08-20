// MEJORA 1: PresetControls.tsx con scroll mejorado

import React, { useEffect, useRef } from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import './PresetControls.css';  // ✅ AÑADIR ESTE IMPORT
import { getNestedValue } from '../utils/objectPath';

interface PresetControlsProps {
  preset: LoadedPreset;
  config: any;
  onConfigUpdate: (path: string, value: any) => void;
}

export const PresetControls: React.FC<PresetControlsProps> = ({
  preset,
  config,
  onConfigUpdate
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  // Detectar si hay overflow para mostrar indicador
  useEffect(() => {
    const checkOverflow = () => {
      if (contentRef.current) {
        const hasOverflow = contentRef.current.scrollHeight > contentRef.current.clientHeight;
        contentRef.current.classList.toggle('has-overflow', hasOverflow);
      }
    };

    checkOverflow();
    window.addEventListener('resize', checkOverflow);
    return () => window.removeEventListener('resize', checkOverflow);
  }, [preset]);

  const handleControlChange = (controlName: string, value: any, type: string) => {
    let processedValue = value;

    switch (type) {
      case 'number':
      case 'slider':
        processedValue = parseFloat(value);
        break;
      case 'boolean':
        processedValue = Boolean(value);
        break;
      case 'color':
        // Convertir hex a RGB normalizado
        const hex = value.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16) / 255;
        const g = parseInt(hex.substr(2, 2), 16) / 255;
        const b = parseInt(hex.substr(4, 2), 16) / 255;
        processedValue = [r, g, b];
        break;
    }

    onConfigUpdate(controlName, processedValue);
  };

  const renderControl = (control: any) => {
    const currentValue = getNestedValue(config, control.name) ?? control.default;

    switch (control.type) {
      case 'slider':
        return (
          <div key={control.name} className="control-group">
            <label className="control-label">
              {control.label || control.name}: {currentValue?.toFixed?.(2) || currentValue}
            </label>
            <input
              type="range"
              min={control.min || 0}
              max={control.max || 1}
              step={control.step || 0.01}
              value={currentValue || control.default || 0}
              onChange={(e) => handleControlChange(control.name, e.target.value, 'slider')}
              className="control-slider"
            />
            <div className="slider-range">
              <span className="range-min">{control.min || 0}</span>
              <span className="range-max">{control.max || 1}</span>
            </div>
          </div>
        );
      
      case 'number':
        return (
          <div key={control.name} className="control-group">
            <label className="control-label">{control.label || control.name}</label>
            <input
              type="number"
              min={control.min}
              max={control.max}
              step={control.step || 1}
              value={currentValue || control.default || 0}
              onChange={(e) => handleControlChange(control.name, e.target.value, 'number')}
              className="control-number"
            />
          </div>
        );
      
      case 'color':
        const colorHex = Array.isArray(currentValue) 
          ? `#${Math.round(currentValue[0] * 255).toString(16).padStart(2, '0')}${Math.round(currentValue[1] * 255).toString(16).padStart(2, '0')}${Math.round(currentValue[2] * 255).toString(16).padStart(2, '0')}`
          : currentValue || control.default || '#ffffff';
        
        return (
          <div key={control.name} className="control-group">
            <label className="control-label">{control.label || control.name}</label>
            <div className="color-control-wrapper">
              <input
                type="color"
                value={colorHex}
                onChange={(e) => handleControlChange(control.name, e.target.value, 'color')}
                className="control-color"
              />
              <span className="color-value">{colorHex.toUpperCase()}</span>
            </div>
          </div>
        );
      
      case 'boolean':
        return (
          <div key={control.name} className="control-group">
            <label className="control-label checkbox-label">
              <input
                type="checkbox"
                checked={currentValue || control.default || false}
                onChange={(e) => handleControlChange(control.name, e.target.checked, 'boolean')}
                className="control-checkbox"
              />
              {control.label || control.name}
            </label>
          </div>
        );
      
      case 'select':
        return (
          <div key={control.name} className="control-group">
            <label className="control-label">{control.label || control.name}</label>
            <select
              value={currentValue || control.default || ''}
              onChange={(e) => handleControlChange(control.name, e.target.value, 'select')}
              className="control-select"
            >
              {control.options?.map((option: string) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        );
      
      case 'text':
        return (
          <div key={control.name} className="control-group">
            <label className="control-label">{control.label || control.name}</label>
            <input
              type="text"
              value={currentValue?.toString() || control.default?.toString() || ''}
              onChange={(e) => handleControlChange(control.name, e.target.value, 'text')}
              className="control-text"
              placeholder={control.placeholder}
            />
          </div>
        );
      
      default:
        return (
          <div key={control.name} className="control-group">
            <label className="control-label">{control.label || control.name}</label>
            <input
              type="text"
              value={currentValue?.toString() || control.default?.toString() || ''}
              onChange={(e) => handleControlChange(control.name, e.target.value, 'text')}
              className="control-text"
            />
          </div>
        );
    }
  };

  const basicControls = [
    { name: 'width', type: 'number', label: 'Ancho', min: 100, max: 4096, default: getNestedValue(config, 'width') ?? preset.config.defaultConfig?.width ?? 1920 },
    { name: 'height', type: 'number', label: 'Alto', min: 100, max: 4096, default: getNestedValue(config, 'height') ?? preset.config.defaultConfig?.height ?? 1080 },
    { name: 'zoom', type: 'slider', label: 'Zoom', min: 0.1, max: 5, step: 0.1, default: getNestedValue(config, 'zoom') ?? preset.config.defaultConfig?.zoom ?? 1 },
  ];

  const audioControls = [
    { name: 'audioSensitivity', type: 'slider', label: 'Sensibilidad', min: 0, max: 2, step: 0.01, default: getNestedValue(config, 'audioSensitivity') ?? preset.config.defaultConfig?.audioSensitivity ?? 1 },
    { name: 'audioSmoothness', type: 'slider', label: 'Suavizado', min: 0, max: 1, step: 0.01, default: getNestedValue(config, 'audioSmoothness') ?? preset.config.defaultConfig?.audioSmoothness ?? 0.5 },
    { name: 'audioReactivity', type: 'slider', label: 'Reactividad', min: 0, max: 2, step: 0.01, default: getNestedValue(config, 'audioReactivity') ?? preset.config.defaultConfig?.audioReactivity ?? 1 },
  ];

  return (
    <>
      <div className="controls-panel-header">
        <div className="preset-header">
          <h3>{preset.config.name}</h3>
          <div className="preset-meta-line">v{preset.config.version} • {preset.config.category}</div>
          {preset.config.tags && (
            <div className="preset-tags-line">
              {preset.config.tags.join(', ')}
            </div>
          )}
          <p className="preset-description">{preset.config.description}</p>
          <div className="preset-meta">
            <span className="preset-meta-line">📁 {preset.config.category} | 🏷️ {preset.config.tags?.join(', ')}</span>
            <span className="preset-meta-line">👤 {preset.config.author} | 📦 v{preset.config.version}</span>
          </div>
        </div>
      </div>

      <div className="controls-panel-content" ref={contentRef}>
        <div className="preset-controls-container">
          {/* Configuración Básica */}
          <div className="section">
            <div className="section-title">📐 Configuración Básica</div>
            {basicControls.map(control => renderControl(control))}
          </div>

          <div className="section-divider" />

          {/* Controles de Audio */}
          <div className="section">
            <div className="section-title">🎵 Audio</div>
            {audioControls.map(control => renderControl(control))}
          </div>

          <div className="section-divider" />

          {/* Controles Específicos del Preset */}
          {preset.config.controls && preset.config.controls.length > 0 && (
            <>
              <div className="section">
                <div className="section-title">🎨 Controles Específicos</div>
                {preset.config.controls.map((control: any) => renderControl(control))}
              </div>

              <div className="section-divider" />
            </>
          )}

          {/* Mapeo de Audio */}
          {preset.config.audioMapping && (
            <>
              <div className="section">
                <div className="section-title">🎤 Mapeo de Audio</div>
                <div className="audio-mapping">
                  {Object.entries(preset.config.audioMapping).map(([freq, mapping]: [string, any]) => (
                    <div key={freq} className="mapping-item">
                      <div className="mapping-freq">{freq.toUpperCase()}</div>
                      <div className="mapping-desc">{mapping.description}</div>
                      <div className="mapping-effect">{mapping.effect}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="section-divider" />
            </>
          )}

          {/* Información del Preset */}
          <div className="section">
            <div className="section-title">ℹ️ Información</div>
            <div className="preset-info">
              <div className="info-item">
                <span className="info-label">MIDI Note:</span>
                <span className="info-value">{preset.config.note || 'No asignada'}</span>
              </div>
              {preset.config.performance && (
                <div className="info-item">
                  <span className="info-label">Rendimiento:</span>
                  <span className={`performance-badge ${preset.config.performance.complexity || 'medium'}`}>
                    {String(preset.config.performance.complexity || 'medium').toUpperCase()}
                  </span>
                </div>
              )}
              {preset.config.performance?.gpuIntensive && (
                <div className="info-item">
                  <span className="info-label">GPU:</span>
                  <span className="info-value">Intensivo</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
