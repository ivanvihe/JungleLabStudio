import React from 'react';

interface DeviceOption {
  id: string;
  label: string;
}

interface LaunchpadSettingsProps {
  launchpadDevices: DeviceOption[];
  selectedLaunchpadId: string | null;
  onSelectLaunchpad: (id: string | null) => void;
  launchpadChannel: number;
  onLaunchpadChannelChange: (value: number) => void;
  launchpadNote: number;
  onLaunchpadNoteChange: (value: number) => void;
  launchpadSmoothness: number;
  onLaunchpadSmoothnessChange: (value: number) => void;
}

export const LaunchpadSettings: React.FC<LaunchpadSettingsProps> = ({
  launchpadDevices,
  selectedLaunchpadId,
  onSelectLaunchpad,
  launchpadChannel,
  onLaunchpadChannelChange,
  launchpadNote,
  onLaunchpadNoteChange,
  launchpadSmoothness,
  onLaunchpadSmoothnessChange
}) => {
  return (
    <>
      <h4>LaunchPad MIDI</h4>
      <div className="setting-group">
        <label className="setting-label">
          <span>Selecciona LaunchPad</span>
          <select
            value={selectedLaunchpadId || ''}
            onChange={(e) => onSelectLaunchpad(e.target.value || null)}
          >
            <option value="">Ninguno</option>
            {launchpadDevices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Canal LaunchPad Toggle</span>
          <input
            type="number"
            min={1}
            max={16}
            value={launchpadChannel}
            onChange={(e) =>
              onLaunchpadChannelChange(parseInt(e.target.value) || 1)
            }
            className="setting-number"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Nota LaunchPad Toggle</span>
          <input
            type="number"
            min={0}
            max={127}
            value={launchpadNote}
            onChange={(e) =>
              onLaunchpadNoteChange(parseInt(e.target.value) || 0)
            }
            className="setting-number"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Suavizado LaunchPad: {(launchpadSmoothness * 100).toFixed(0)}%</span>
          <input
            type="range"
            min={0}
            max={0.9}
            step={0.05}
            value={launchpadSmoothness}
            onChange={(e) =>
              onLaunchpadSmoothnessChange(parseFloat(e.target.value))
            }
            className="setting-slider"
          />
        </label>
      </div>
    </>
  );
};

