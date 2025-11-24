import { VisualPreset, Parameter, MidiMapping } from '../types';

interface ControlPanelProps {
  presets: VisualPreset[];
  presetId: string;
  onPresetChange: (id: string) => void;
  values: Record<string, number>;
  onChange: (key: string, value: number) => void;
  midi: {
    enabled: boolean;
    status: string;
    learning: string | null;
    mappings: Record<string, MidiMapping>;
    start: () => Promise<void>;
    learn: (key: string) => void;
    stopLearning: () => void;
    inputs: MIDIInput[];
    selectedInputId: string | null;
    selectInput: (id: string) => void;
  };
  audio: {
    enabled: boolean;
    level: number;
    error: string | null;
    devices: MediaDeviceInfo[];
    selectedDeviceId: string | null;
    start: (deviceId?: string) => Promise<void>;
    selectDevice: (deviceId: string) => void;
  };
  orientation: 'landscape' | 'portrait';
  onOrientationChange: (orientation: 'landscape' | 'portrait') => void;
}

const ParameterControl = ({
  parameter,
  value,
  onChange,
  onLearn,
  isLearning,
  mapping,
}: {
  parameter: Parameter;
  value: number;
  onChange: (value: number) => void;
  onLearn: () => void;
  isLearning: boolean;
  mapping?: MidiMapping;
}) => (
  <div className={`parameter ${isLearning ? 'midi-learning' : ''}`}>
    <div className="label">{parameter.label}</div>
    <div className="mapping">
      {mapping ? `CC${mapping.control} ch${mapping.channel + 1}` : 'Sin mapping'}
    </div>
    <input
      className="slider"
      type="range"
      min={parameter.min}
      max={parameter.max}
      step={parameter.step ?? 0.01}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
    />
    <button className="button" onClick={onLearn}>
      {isLearning ? 'Escuchando…' : 'Learn'}
    </button>
    {parameter.description && <div className="description">{parameter.description}</div>}
  </div>
);

export const ControlPanel = ({
  presets,
  presetId,
  onPresetChange,
  values,
  onChange,
  midi,
  audio,
  orientation,
  onOrientationChange,
}: ControlPanelProps) => (
  <aside className="control-panel">
    <div className="header">
      <div className="title">JungleLab Visuals</div>
      <div className="subtitle">Visuales inmersivos con p5.js, audio reactividad y MIDI Learn.</div>
    </div>

    <div className="select-row">
      <select value={presetId} onChange={(e) => onPresetChange(e.target.value)}>
        {presets.map((preset) => (
          <option key={preset.id} value={preset.id}>
            {preset.name}
          </option>
        ))}
      </select>
    </div>

    <div className="status-row">
      <span className="badge">{midi.status}</span>
      <span className="badge">Audio: {audio.enabled ? 'Activo' : 'Detenido'}</span>
      <span className="badge">Nivel: {(audio.level * 100).toFixed(0)}%</span>
    </div>
    {audio.error && <div className="subtitle">{audio.error}</div>}

    <div className="section">
      <button className="button" onClick={() => audio.start(audio.selectedDeviceId ?? undefined)} disabled={audio.enabled}>
        {audio.enabled ? 'Micrófono activo' : 'Habilitar micrófono'}
      </button>
      <div className="select-row">
        <select
          value={audio.selectedDeviceId ?? ''}
          onChange={(e) => audio.selectDevice(e.target.value)}
          disabled={!audio.devices.length}
        >
          {audio.devices.map((device) => (
            <option key={device.deviceId} value={device.deviceId}>
              {device.label || device.deviceId}
            </option>
          ))}
        </select>
        <button className="button" onClick={() => audio.start(audio.selectedDeviceId ?? undefined)}>
          Reiniciar entrada
        </button>
      </div>
      <div className="hint-legend">
        <span><span className="dot" style={{ background: '#5ef4ff' }} /> atmósferas</span>
        <span><span className="dot" style={{ background: '#ff2fb1' }} /> partículas</span>
        <span><span className="dot" style={{ background: '#92ff9f' }} /> cintas/ondas</span>
      </div>
    </div>

    <div className="section">
      <div className="select-row">
        <select
          value={midi.selectedInputId ?? ''}
          onChange={(e) => midi.selectInput(e.target.value)}
          disabled={!midi.inputs.length}
        >
          {midi.inputs.map((input) => (
            <option key={input.id} value={input.id}>
              {input.name || input.id}
            </option>
          ))}
        </select>
        <button className="button" onClick={midi.start} disabled={midi.enabled}>
          {midi.enabled ? 'MIDI listo' : 'Activar MIDI'}
        </button>
      </div>
    </div>

    <div className="section">
      <div className="select-row">
        <div className="title">Orientación</div>
        <div className="select-row" style={{ gap: '0.5rem' }}>
          <button
            className="button"
            onClick={() => onOrientationChange('landscape')}
            disabled={orientation === 'landscape'}
          >
            Horizontal 16:9
          </button>
          <button
            className="button"
            onClick={() => onOrientationChange('portrait')}
            disabled={orientation === 'portrait'}
          >
            Vertical 9:16
          </button>
        </div>
      </div>
    </div>

    <div className="section">
      {presets
        .find((p) => p.id === presetId)
        ?.parameters.map((parameter) => (
          <ParameterControl
            key={parameter.key}
            parameter={parameter}
            value={values[parameter.key] ?? parameter.defaultValue}
            onChange={(val) => onChange(parameter.key, val)}
            onLearn={() => midi.learning === parameter.key ? midi.stopLearning() : midi.learn(parameter.key)}
            isLearning={midi.learning === parameter.key}
            mapping={midi.mappings[parameter.key]}
          />
        ))}
    </div>
  </aside>
);
