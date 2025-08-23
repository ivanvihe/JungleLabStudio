import React, { useState } from 'react';
import { CreaLabProject, GenerativeTrack, TrackType } from '../types/CrealabTypes';
import { TopBar } from './TopBar';
import LaunchControlVisualizer from './LaunchControlVisualizer';
import useLaunchControlXL from '../hooks/useLaunchControlXL';
import { useMidiDevices } from '../hooks/useMidiDevices';
import GeneratorControls from './GeneratorControls';
import BassGeneratorControls from './BassGeneratorControls';
import { InstrumentSelector } from './InstrumentSelector';
import MidiConfiguration from './MidiConfiguration';
import ProjectManager from './ProjectManager';
import './CreaLab.css';

interface CreaLabProps {
  onSwitchToAudioVisualizer: () => void;
}

const TRACK_COLORS = [
  '#ff6b6b',
  '#ffa94d',
  '#ffd43b',
  '#69db7c',
  '#4dabf7',
  '#845ef7',
  '#f06595',
  '#94d82d'
];

const DEFAULT_TRACK_TYPES: TrackType[] = [
  'kick',
  'bass',
  'arp',
  'lead',
  'fx',
  'perc',
  'visual',
  'lead'
];

const createDefaultTrack = (n: number): GenerativeTrack => ({
  id: `track-${n}`,
  name: `Track ${n}`,
  trackNumber: n,
  color: TRACK_COLORS[(n - 1) % TRACK_COLORS.length],
  trackType: DEFAULT_TRACK_TYPES[(n - 1) % DEFAULT_TRACK_TYPES.length],
  outputDevice: '',
  midiChannel: 1,
  generator: {
    type: 'off',
    enabled: false,
    parameters: {},
    lastNoteTime: 0,
    currentStep: 0
  },
  controls: {
    intensity: 0,
    paramA: 0,
    paramB: 0,
    paramC: 0,
    playStop: false,
    mode: 0
  },
  launchControlMapping: {
    stripNumber: n,
    faderCC: 0,
    knob1CC: 0,
    knob2CC: 0,
    knob3CC: 0,
    button1CC: 0,
    button2CC: 0
  }
});

export const CreaLab: React.FC<CreaLabProps> = ({ onSwitchToAudioVisualizer }) => {
  const controller = useLaunchControlXL();
  const { outputDevices } = useMidiDevices();
  const [showMidiConfig, setShowMidiConfig] = useState(false);
  const [showProjectManager, setShowProjectManager] = useState(false);
  const [project, setProject] = useState<CreaLabProject>({
    id: 'project-1',
    name: 'New Project',
    tracks: [
      createDefaultTrack(1),
      createDefaultTrack(2),
      createDefaultTrack(3),
      createDefaultTrack(4),
      createDefaultTrack(5),
      createDefaultTrack(6),
      createDefaultTrack(7),
      createDefaultTrack(8)
    ],
    globalTempo: 120,
    key: 'C',
    scale: 'minor',
    genre: 'default',
    transport: {
      isPlaying: false,
      isPaused: false,
      currentBeat: 0,
      currentBar: 0,
      currentStep: 0
    },
    launchControl: {
      connected: false
    },
    midiClock: {
      enabled: false,
      source: 'internal',
      ppqn: 24
    }
  });

  const updateTrackName = (trackNumber: number, name: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber ? { ...t, name } : t
      ) as any
    }));
  };

  const updateMidiChannel = (trackNumber: number, channel: number) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber ? { ...t, midiChannel: channel } : t
      ) as any
    }));
  };

  const updateOutputDevice = (trackNumber: number, deviceId: string) => {
    const device = outputDevices.find(d => d.id === deviceId);
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, outputDevice: deviceId, outputDeviceName: device?.name || '' }
          : t
      ) as any
    }));
  };

  const updateTrackType = (trackNumber: number, type: TrackType) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber ? { ...t, trackType: type } : t
      ) as any
    }));
  };

  const updateTrackControls = (
    trackNumber: number,
    changes: Partial<GenerativeTrack['controls']>
  ) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, controls: { ...t.controls, ...changes } }
          : t
      ) as any
    }));
  };

  const updateGeneratorParameters = (
    trackNumber: number,
    params: Record<string, any>
  ) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, generator: { ...t.generator, parameters: params } }
          : t
      ) as any
    }));
  };

  const updateGeneratorType = (trackNumber: number, type: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, generator: { ...t.generator, type: type as any } }
          : t
      ) as any
    }));
  };

  const applyTrackUpdates = (trackNumber: number, updates: Partial<GenerativeTrack>) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber ? { ...t, ...updates } : t
      ) as any
    }));
  };

  return (
    <div className="crealab-container">
      <TopBar
        projectName={project.name}
        tempo={project.globalTempo}
        onTempoChange={tempo => setProject(p => ({ ...p, globalTempo: tempo }))}
        keySignature={project.key}
        onKeyChange={key => setProject(p => ({ ...p, key }))}
        onSwitchToAudioVisualizer={onSwitchToAudioVisualizer}
      />

      <button className="open-midi-config" onClick={() => setShowMidiConfig(true)}>MIDI Config</button>
      <button className="open-project-manager" onClick={() => setShowProjectManager(true)}>Projects</button>

      <LaunchControlVisualizer controller={controller} />

      <main className="crealab-workspace">
        <div className="tracks-grid">
          {project.tracks.map(track => (
            <div
              key={track.id}
              className="track-strip"
              style={{ ['--track-color' as any]: track.color }}
            >
              <div className="track-header">
                <div className="track-number">{track.trackNumber}</div>
                <input
                  className="track-name-input"
                  value={track.name}
                  onChange={e => updateTrackName(track.trackNumber, e.target.value)}
                />
              </div>

              <div className="track-controls">
                <select
                  className="track-type-selector"
                  value={track.trackType}
                  onChange={e =>
                    updateTrackType(track.trackNumber, e.target.value as TrackType)
                  }
                >
                  <option value="kick">Kick</option>
                  <option value="bass">Bass</option>
                  <option value="arp">Arp</option>
                  <option value="lead">Lead</option>
                  <option value="fx">FX</option>
                  <option value="perc">Perc</option>
                  <option value="visual">Visual</option>
                </select>

                <InstrumentSelector
                  track={track}
                  onTrackUpdate={updates => applyTrackUpdates(track.trackNumber, updates)}
                  genre={project.genre}
                  allTracks={project.tracks}
                />
                <div className="midi-config">
                  <select
                    className="device-selector"
                    value={track.outputDevice}
                    onChange={e => updateOutputDevice(track.trackNumber, e.target.value)}
                  >
                    <option value="">Device</option>
                    {outputDevices.map(dev => (
                      <option key={dev.id} value={dev.id}>{dev.name}</option>
                    ))}
                  </select>
                  <select
                    className="channel-selector"
                    value={track.midiChannel}
                    onChange={e =>
                      updateMidiChannel(track.trackNumber, parseInt(e.target.value))
                    }
                  >
                    {Array.from({ length: 16 }, (_, i) => i + 1).map(ch => (
                      <option key={ch} value={ch}>{ch}</option>
                    ))}
                  </select>
                </div>

                <div className="generator-config">
                  <select
                    className="generator-selector"
                    value={track.generator.type}
                    onChange={e => updateGeneratorType(track.trackNumber, e.target.value)}
                  >
                    <option value="off">Off</option>
                    <option value="euclidean">Euclidean</option>
                    <option value="probabilistic">Probabilistic</option>
                    <option value="markov">Markov</option>
                    <option value="arpeggiator">Arpeggiator</option>
                    <option value="chaos">Chaos</option>
                    <option value="magenta">Magenta</option>
                  </select>
                </div>

                {track.trackType === 'bass' && (
                  <BassGeneratorControls
                    track={track}
                    onParametersChange={params =>
                      updateGeneratorParameters(track.trackNumber, params)
                    }
                  />
                )}

                <GeneratorControls
                  track={track}
                  onChange={changes =>
                    updateTrackControls(track.trackNumber, changes)
                  }
                />

                <div className="launch-control-preview">
                  <div className="lc-controls">
                    <div className="lc-knobs">
                      <div className="lc-knob"><span className="knob-value">{track.controls.paramA}</span></div>
                      <div className="lc-knob"><span className="knob-value">{track.controls.paramB}</span></div>
                      <div className="lc-knob"><span className="knob-value">{track.controls.paramC}</span></div>
                    </div>
                    <div className="lc-fader">
                      <div className="fader-track">
                        <div
                          className="fader-thumb"
                          style={{ bottom: `${(track.controls.intensity / 127) * 60}px` }}
                        />
                      </div>
                      <div className="fader-value">{track.controls.intensity}</div>
                    </div>
                    <div className="lc-buttons">
                      <button className={`lc-button ${track.controls.playStop ? 'active' : ''}`}>▶</button>
                      <button className={`lc-button ${track.controls.mode ? 'active' : ''}`}>M</button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="track-status">
                <div
                  className={`generator-status ${track.generator.enabled ? 'active' : 'inactive'}`}
                >
                  {track.generator.enabled ? track.generator.type : 'inactive'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
      {showMidiConfig && <MidiConfiguration onClose={() => setShowMidiConfig(false)} />}
      {showProjectManager && (
        <ProjectManager
          project={project}
          onProjectLoad={setProject}
          onClose={() => setShowProjectManager(false)}
        />
      )}
    </div>
  );
};

export default CreaLab;

