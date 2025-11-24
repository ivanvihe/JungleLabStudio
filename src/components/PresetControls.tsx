import React from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { getNestedValue } from '../utils/objectPath';
import {
  SliderControl,
  TextControl,
  ColorControl,
  CheckboxControl,
  SelectControl,
} from './controls';
import MidiNoteControl from './controls/MidiNoteControl';
import './PresetControls.css';
import { useMidiContext } from '../contexts/MidiContext';

interface ControlRendererProps {
  control: any;
  value: any;
  id: string;
  onChange: (value: any) => void;
  isReadOnly: boolean;
  isCustomTextPreset?: boolean;
  path: string;
}

const CONTROL_RENDERERS: Record<string, React.FC<any>> = {
  slider: SliderControl,
  text: TextControl,
  color: ColorControl,
  checkbox: CheckboxControl,
  select: SelectControl,
  'midi-note-recorder': MidiNoteControl,
};


interface PresetControlsProps {
  preset: LoadedPreset;
  config: Record<string, any>;
  onChange?: (path: string, value: any) => void;
  isReadOnly?: boolean;
  layerId?: string;
}

const PresetControls: React.FC<PresetControlsProps> = ({
  preset,
  config,
  onChange,
  isReadOnly = false,
  layerId
}) => {
  const {
    startParameterLearn,
    cancelParameterLearn,
    parameterLearnTarget,
    parameterMappings,
    mappedParameterEvent,
    clearParameterMapping,
  } = useMidiContext();

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

  const controlTarget = (controlName: string) => {
    const scope = layerId || 'global';
    return `${scope}:${preset.id}:${controlName}`;
  };

  React.useEffect(() => {
    if (mappedParameterEvent && mappedParameterEvent.target) {
      const [, , controlName] = mappedParameterEvent.target.split(':');
      if (controlName && preset.id && controlTarget(controlName) === mappedParameterEvent.target) {
        handleControlChange(controlName, mappedParameterEvent.value);
      }
    }
  }, [mappedParameterEvent]);

  const renderControl = (control: any) => {
    const value = getControlValue(control.name, control.default);
    const controlId = `${preset.id}-${control.name}`;
    const Renderer = CONTROL_RENDERERS[control.type];
    if (!Renderer) return null;

    const targetId = controlTarget(control.name);
    const mapping = parameterMappings[targetId];
    const isLearning = parameterLearnTarget?.id === targetId;

    return (
      <div key={control.name} className="control-with-midi">
        <div className="control-header">
          <span className="control-title">{control.label}</span>
          {!isReadOnly && (
            <div className="midi-map-buttons">
              <button
                type="button"
                className={`midi-learn ${isLearning ? 'learning' : ''}`}
                onClick={() =>
                  isLearning
                    ? cancelParameterLearn()
                    : startParameterLearn(targetId, {
                        min: control.min,
                        max: control.max,
                        label: control.label,
                      })
                }
              >
                {isLearning ? 'Asignando CC…' : 'Learn'}
              </button>
              {mapping && (
                <button
                  type="button"
                  className="midi-clear"
                  onClick={() => clearParameterMapping(targetId)}
                >
                  CC {mapping.cc}
                </button>
              )}
            </div>
          )}
        </div>
        <Renderer
          control={control}
          value={value}
          id={controlId}
          onChange={(val) => handleControlChange(control.name, val)}
          isReadOnly={isReadOnly}
          isCustomTextPreset={isCustomTextPreset}
          path={control.name}
        />
      </div>
    );
  };
  if (!preset.config.controls || preset.config.controls.length === 0) {
    return (
      <div className="preset-controls no-controls">
        <p>No controls available for this preset.</p>
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
            <small>Instance: {preset.config.name}</small>
          </div>
        </div>
      )}

      <div className="controls-container">
        {preset.config.controls.map(renderControl)}
      </div>

      {preset.config.audioMapping && (
        <div className="audio-mapping">
          <h4>Audio Mapping</h4>
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
          <small>👁️ Preview - Values will apply when added to a layer</small>
        </div>
      )}
    </div>
  );
};

export default PresetControls;