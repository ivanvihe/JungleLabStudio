import React, { useEffect, useState } from 'react';

interface TopBarProps {
  midiActive: boolean;
  midiDeviceName: string | null;
  midiDeviceCount: number;
  bpm: number | null;
  beatActive: boolean;
  audioDeviceName: string | null;
  audioDeviceCount: number;
  audioGain: number;
  onAudioGainChange: (value: number) => void;
  audioLevel: number;
  onFullScreen: () => void;
  onClearAll: () => void;
  onOpenSettings: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  midiActive,
  midiDeviceName,
  midiDeviceCount,
  bpm,
  beatActive,
  audioDeviceName,
  audioDeviceCount,
  audioGain,
  onAudioGainChange,
  audioLevel,
  onFullScreen,
  onClearAll,
  onOpenSettings
}) => {
  const [activeLed, setActiveLed] = useState(0);

  useEffect(() => {
    if (beatActive) {
      setActiveLed(prev => (prev === 0 ? 1 : 0));
    }
  }, [beatActive]);

  return (
    <div className="top-bar">
      <div className="midi-section">
        <div className={`midi-led ${midiActive ? 'active' : ''}`}></div>
        <span className="midi-device">
          {midiDeviceName || `${midiDeviceCount} MIDI dispositivos`}
        </span>
      </div>

      <div className="separator" />

      <div className="bpm-section">
        <span>BPM: {bpm ? bpm.toFixed(1) : '--'}</span>
        <div className="metronome">
          <div className={`metronome-led ${activeLed === 0 ? 'active' : ''}`}></div>
          <div className={`metronome-led ${activeLed === 1 ? 'active' : ''}`}></div>
        </div>
      </div>

      <div className="separator" />

      <div className="audio-section">
        <span className="audio-device">
          {audioDeviceName || `${audioDeviceCount} audio dispositivos`}
        </span>
        <input
          type="range"
          min={0}
          max={2}
          step={0.01}
          value={audioGain}
          onChange={(e) => onAudioGainChange(parseFloat(e.target.value))}
          className="audio-gain-slider"
        />
        <div className="vu-meter">
          <div
            className="vu-fill"
            style={{ width: `${Math.min(audioLevel * 100, 100)}%` }}
          />
        </div>
      </div>

      <div className="separator" />

      <div className="actions-section">
        <button onClick={onFullScreen} alt="Go Full Screen mode!!">Full Screen</button>
        <button onClick={onClearAll}>Clear All</button>
        <button onClick={onOpenSettings}>Settings</button>
      </div>
    </div>
  );
};
