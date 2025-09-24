import React, { useEffect, useState } from 'react';
import { LAUNCHPAD_PRESETS } from '../utils/launchpad';
import './TopBar.css';
import { IconButton } from './ui';

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
  onToggleUi: () => void;
  onClearAll: () => void;
  onOpenSettings: () => void;
  onOpenResources: () => void;
  launchpadAvailable: boolean;
  launchpadOutput: any | null;
  launchpadRunning: boolean;
  launchpadPreset: string;
  onToggleLaunchpad?: () => void;
  launchpadText?: string;
  onLaunchpadTextChange?: (text: string) => void;
  onLaunchpadPresetChange?: (preset: string) => void;
  onToggleSidebar?: () => void;
  isSidebarCollapsed?: boolean;
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
  onToggleUi,
  onClearAll,
  onOpenSettings,
  onOpenResources,
  launchpadAvailable,
  launchpadOutput,
  launchpadRunning,
  launchpadPreset,
  onToggleLaunchpad,
  onLaunchpadPresetChange,
  launchpadText,
  onLaunchpadTextChange,
  onToggleSidebar,
  isSidebarCollapsed,
}) => {
  const [activeLed, setActiveLed] = useState(0);

  useEffect(() => {
    if (beatActive) {
      setActiveLed(prev => (prev === 0 ? 1 : 0));
    }
  }, [beatActive]);

  return (
    <div className="top-bar">
      <div className="top-bar__cluster">
        {onToggleSidebar && (
          <IconButton
            icon={isSidebarCollapsed ? '☰' : '☰'}
            label={
              isSidebarCollapsed
                ? 'Expandir panel lateral'
                : 'Colapsar panel lateral'
            }
            variant="ghost"
            size="sm"
            onClick={onToggleSidebar}
            className="top-bar__menu-toggle"
          />
        )}

        <div className="midi-section">
          <div className={`midi-led ${midiActive ? 'active' : ''}`}></div>
          <span className="midi-device">
            {midiDeviceName || `${midiDeviceCount} MIDI devices`}
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
      </div>

      <div className="separator" />

      <div className="audio-section">
        <span className="audio-device">
          {audioDeviceName || `${audioDeviceCount} audio devices`}
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

      <div className="top-bar-spacer" />

      <div className="actions-section">
        <IconButton
          icon="🗂️"
          label="Abrir galería completa"
          onClick={onOpenResources}
          variant="ghost"
          size="sm"
        />
        <IconButton
          icon="🗑️"
          label="Limpiar todo"
          onClick={onClearAll}
          variant="danger"
          size="sm"
        />
        <IconButton
          icon="🙈"
          label="Ocultar controles (F10)"
          onClick={onToggleUi}
          variant="ghost"
          size="sm"
        />
        <IconButton
          icon="⛶"
          label="Pantalla completa"
          onClick={onFullScreen}
          variant="ghost"
          size="sm"
        />
        <IconButton
          icon="⚙️"
          label="Preferencias"
          onClick={onOpenSettings}
          variant="ghost"
          size="sm"
        />
      </div>

      <div className="top-bar-spacer" />

      {launchpadAvailable && (
        <>
          <div className="separator" />
          <div className="launchpad-controls">
            <select
              value={launchpadPreset}
              onChange={(e) => onLaunchpadPresetChange?.(e.target.value)}
              className="launchpad-preset-select"
            >
              {LAUNCHPAD_PRESETS.map(p => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
            {launchpadPreset === 'custom-text' && (
              <input
                type="text"
                value={launchpadText || ''}
                onChange={(e) => onLaunchpadTextChange?.(e.target.value)}
              />
            )}
            <IconButton
              icon={launchpadRunning ? '⏹️' : '▶️'}
              label={launchpadRunning ? 'Detener LaunchPad' : 'Iniciar LaunchPad'}
              onClick={() => onToggleLaunchpad?.()}
              variant={launchpadRunning ? 'accent' : 'ghost'}
              size="sm"
              disabled={!launchpadOutput}
              className={`launchpad-button ${launchpadRunning ? 'running' : ''}`}
              title={
                launchpadOutput
                  ? `Toggle LaunchPad (${launchpadOutput.name})`
                  : 'No LaunchPad device available'
              }
            />
          </div>
        </>
      )}
    </div>
  );
};
