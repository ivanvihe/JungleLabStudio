import React from 'react';
import { AVAILABLE_EFFECTS } from '../../utils/effects';

interface DeviceOption {
  id: string;
  label: string;
}

interface MidiClockSettings {
  resolution: number;
  delay: number;
  quantization: number;
  jumpMode: boolean;
  stability: number;
  type: 'midi' | 'internal' | 'off';
}

interface MidiSettingsProps {
  midiDevices: DeviceOption[];
  selectedMidiId: string | null;
  onSelectMidi: (id: string) => void;
  midiClockSettings: MidiClockSettings;
  onUpdateClockSettings: (updates: Partial<MidiClockSettings>) => void;
  internalBpm: number;
  onSetInternalBpm: (bpm: number) => void;
  clockStable: boolean;
  currentMeasure: number;
  currentBeat: number;
  layerChannels: Record<string, number>;
  onLayerChannelChange: (layerId: string, channel: number) => void;
  effectMidiNotes: Record<string, number>;
  onEffectMidiNoteChange: (effect: string, note: number) => void;
}

const RESOLUTION_OPTIONS = [
  { value: 24, label: '24 PPQ (Standard)' },
  { value: 48, label: '48 PPQ (High)' },
  { value: 96, label: '96 PPQ (Ultra)' },
  { value: 192, label: '192 PPQ (Maximum)' },
];

const QUANTIZATION_OPTIONS = [
  { value: 1, label: '1/4 (Quarter Note)' },
  { value: 2, label: '1/2 (Half Note)' },
  { value: 4, label: '1/1 (Whole Note)' },
  { value: 8, label: '2 Bars' },
  { value: 16, label: '4 Bars' },
];

export const MidiSettings: React.FC<MidiSettingsProps> = ({
  midiDevices,
  selectedMidiId,
  onSelectMidi,
  midiClockSettings,
  onUpdateClockSettings,
  internalBpm,
  onSetInternalBpm,
  clockStable,
  currentMeasure,
  currentBeat,
  layerChannels,
  onLayerChannelChange,
  effectMidiNotes,
  onEffectMidiNoteChange,
}) => {
  return (
    <>
      <h3>🎛️ Hardware MIDI</h3>

      <h4>🕒 MIDI Clock & Synchronización</h4>

      {/* Device Selection */}
      <div className="setting-group">
        <label className="setting-label">
          <span>Dispositivo MIDI</span>
          <select
            value={selectedMidiId || ''}
            onChange={e => onSelectMidi(e.target.value)}
            className="setting-select"
          >
            <option value="">Seleccionar dispositivo...</option>
            {midiDevices.map(dev => (
              <option key={dev.id} value={dev.id}>
                {dev.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Clock Type */}
      <div className="setting-group">
        <label className="setting-label">
          <span>Modo de Clock</span>
          <select
            value={midiClockSettings.type}
            onChange={e =>
              onUpdateClockSettings({ type: e.target.value as 'midi' | 'internal' | 'off' })
            }
            className="setting-select"
          >
            <option value="midi">MIDI Clock Externo</option>
            <option value="internal">Clock Interno</option>
            <option value="off">Deshabilitado</option>
          </select>
        </label>
      </div>

      {/* Internal BPM Control */}
      {midiClockSettings.type === 'internal' && (
        <div className="setting-group">
          <label className="setting-label">
            <span>BPM Interno</span>
            <input
              type="number"
              min={60}
              max={200}
              value={internalBpm}
              onChange={e => onSetInternalBpm(parseInt(e.target.value) || 120)}
              className="setting-number"
            />
          </label>
        </div>
      )}

      {/* Clock Resolution */}
      <div className="setting-group">
        <label className="setting-label">
          <span>Resolución (PPQ)</span>
          <select
            value={midiClockSettings.resolution}
            onChange={e => onUpdateClockSettings({ resolution: parseInt(e.target.value) })}
            className="setting-select"
          >
            {RESOLUTION_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <small className="setting-help">
          Mayor resolución = mayor precisión pero más carga CPU
        </small>
      </div>

      {/* Delay Compensation */}
      <div className="setting-group">
        <label className="setting-label">
          <span>Delay Compensación (ms)</span>
          <input
            type="number"
            min={-50}
            max={100}
            value={midiClockSettings.delay}
            onChange={e =>
              onUpdateClockSettings({ delay: parseInt(e.target.value) || 0 })
            }
            className="setting-number"
          />
        </label>
        <small className="setting-help">
          Ajusta el timing si los visuales van adelantados (-) o retrasados (+)
        </small>
      </div>

      {/* BPM Stability */}
      <div className="setting-group">
        <label className="setting-label">
          <span>Estabilidad BPM</span>
          <input
            type="range"
            min={1}
            max={10}
            value={midiClockSettings.stability}
            onChange={e =>
              onUpdateClockSettings({ stability: parseInt(e.target.value) })
            }
            className="setting-range"
          />
          <span className="range-value">{midiClockSettings.stability}</span>
        </label>
        <small className="setting-help">
          1 = Respuesta rápida, 10 = Máxima estabilidad
        </small>
      </div>

      {/* Quantization */}
      <div className="setting-group">
        <label className="setting-label">
          <span>Cuantización Visual</span>
          <select
            value={midiClockSettings.quantization}
            onChange={e =>
              onUpdateClockSettings({ quantization: parseInt(e.target.value) })
            }
            className="setting-select"
          >
            {QUANTIZATION_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <small className="setting-help">
          Los cambios visuales se disparan solo en estos intervalos
        </small>
      </div>

      {/* Jump Mode */}
      <div className="setting-group">
        <label className="setting-label checkbox-label">
          <input
            type="checkbox"
            checked={midiClockSettings.jumpMode}
            onChange={e => onUpdateClockSettings({ jumpMode: e.target.checked })}
            className="setting-checkbox"
          />
          <span>Modo Jump por Compases</span>
        </label>
        <small className="setting-help">
          Cambios de preset automáticos cada compás (4 beats)
        </small>
      </div>

      {/* Clock Status Display */}
      <div className="clock-status">
        <h5>Estado del Clock</h5>
        <div className="status-grid">
          <div className="status-item">
            <span className="status-label">Estado:</span>
            <span
              className={`status-value ${clockStable ? 'stable' : 'unstable'}`}
            >
              {clockStable ? '🟢 Estable' : '🟡 Sincronizando...'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Compás:</span>
            <span className="status-value">{currentMeasure}</span>
          </div>
          <div className="status-item">
            <span className="status-label">Beat:</span>
            <span className="status-value">{currentBeat}/4</span>
          </div>
        </div>
      </div>

      <div className="setting-divider" />

      <h4>🎹 MIDI para Pads</h4>

      {/* Layer Channel Settings */}
      <div className="layer-channel-settings">
        <h5>Canal MIDI por Layer</h5>
        {['A', 'B', 'C'].map(id => (
          <label key={id} className="setting-label">
            <span>Layer {id}</span>
            <input
              type="number"
              min={1}
              max={16}
              value={layerChannels[id]}
              onChange={e =>
                onLayerChannelChange(id, parseInt(e.target.value) || 1)
              }
              className="setting-number"
            />
          </label>
        ))}
      </div>

      {/* Effect MIDI Notes */}
      <div className="effect-note-settings">
        <h5>Notas MIDI por Efecto</h5>
        <div className="effects-grid">
          {AVAILABLE_EFFECTS.filter(eff => eff !== 'none').map(eff => (
            <label key={eff} className="setting-label effect-setting">
              <span className="effect-name">{eff}</span>
              <input
                type="number"
                min={0}
                max={127}
                value={effectMidiNotes[eff] ?? 0}
                onChange={e =>
                  onEffectMidiNoteChange(eff, parseInt(e.target.value) || 0)
                }
                className="setting-number small"
              />
            </label>
          ))}
        </div>
      </div>

      <style jsx>{`
        .setting-divider {
          margin: 20px 0;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .setting-help {
          display: block;
          margin-top: 4px;
          color: rgba(255, 255, 255, 0.6);
          font-size: 11px;
          line-height: 1.3;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .setting-range {
          flex: 1;
          margin-right: 8px;
        }

        .range-value {
          min-width: 20px;
          text-align: center;
          font-weight: 600;
        }

        .clock-status {
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 6px;
          padding: 12px;
          margin: 12px 0;
        }

        .status-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 8px;
        }

        .status-item {
          text-align: center;
        }

        .status-label {
          display: block;
          font-size: 11px;
          opacity: 0.7;
        }

        .status-value {
          font-weight: 600;
        }

        .status-value.stable {
          color: #4caf50;
        }

        .status-value.unstable {
          color: #fbc02d;
        }

        .effects-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 8px;
        }

        .effect-setting {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .effect-name {
          text-transform: capitalize;
        }

        .setting-number.small {
          width: 60px;
        }
      `}</style>
    </>
  );
};

