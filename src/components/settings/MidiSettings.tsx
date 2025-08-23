import React from 'react';
import { AVAILABLE_EFFECTS } from '../../utils/effects';

interface DeviceOption {
  id: string;
  label: string;
}

interface MidiSettingsProps {
  midiDevices: DeviceOption[];
  selectedMidiId: string | null;
  onSelectMidi: (id: string) => void;
  midiClockDelay: number;
  onMidiClockDelayChange: (value: number) => void;
  midiClockType: string;
  onMidiClockTypeChange: (value: string) => void;
  layerChannels: Record<string, number>;
  onLayerChannelChange: (layerId: string, channel: number) => void;
  effectMidiNotes: Record<string, number>;
  onEffectMidiNoteChange: (effect: string, note: number) => void;
}

export const MidiSettings: React.FC<MidiSettingsProps> = ({
  midiDevices,
  selectedMidiId,
  onSelectMidi,
  midiClockDelay,
  onMidiClockDelayChange,
  midiClockType,
  onMidiClockTypeChange,
  layerChannels,
  onLayerChannelChange,
  effectMidiNotes,
  onEffectMidiNoteChange
}) => {
  return (
    <>
      <h3>🎛️ Hardware MIDI</h3>

      <h4>Audio MIDI (Clock)</h4>
      <div className="setting-group">
        <label className="setting-label">
          <span>Dispositivo MIDI</span>
          <select
            value={selectedMidiId || ''}
            onChange={(e) => onSelectMidi(e.target.value)}
            className="setting-select"
          >
            <option value="">Por Defecto</option>
            {midiDevices.map((dev) => (
              <option key={dev.id} value={dev.id}>
                {dev.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Tipo de Clock</span>
          <select
            value={midiClockType}
            onChange={(e) => onMidiClockTypeChange(e.target.value)}
            className="setting-select"
          >
            <option value="midi">MIDI</option>
            <option value="off">Off</option>
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Delay Clock (ms)</span>
          <input
            type="number"
            min={0}
            max={1000}
            value={midiClockDelay}
            onChange={(e) =>
              onMidiClockDelayChange(parseInt(e.target.value) || 0)
            }
            className="setting-number"
          />
        </label>
      </div>

      <h4>MIDI for Pads</h4>
      <div className="layer-channel-settings">
        <h5>Canal MIDI por Layer</h5>
        {['A', 'B', 'C'].map((id) => (
          <label key={id} className="setting-label">
            <span>Layer {id}</span>
            <input
              type="number"
              min={1}
              max={16}
              value={layerChannels[id]}
              onChange={(e) =>
                onLayerChannelChange(id, parseInt(e.target.value) || 1)
              }
              className="setting-number"
            />
          </label>
        ))}
      </div>
      <div className="effect-note-settings">
        <h5>Notas MIDI por Efecto</h5>
        {AVAILABLE_EFFECTS.filter((eff) => eff !== 'none').map((eff) => (
          <label key={eff} className="setting-label effect-setting">
            <span>{eff}</span>
            <input
              type="number"
              min={0}
              max={127}
              value={effectMidiNotes[eff] ?? 0}
              onChange={(e) =>
                onEffectMidiNoteChange(
                  eff,
                  parseInt(e.target.value) || 0
                )
              }
              className="setting-number"
            />
          </label>
        ))}
      </div>
    </>
  );
};

