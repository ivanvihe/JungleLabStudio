import React, { useState, useEffect } from 'react';
import { CreaLabProject, GenerativeTrack, TrackType, GeneratorType } from '../types/CrealabTypes';
import { TopBar } from './TopBar';
import LaunchControlStrip from './LaunchControlStrip';
import useLaunchControlXL from '../hooks/useLaunchControlXL';
import { SessionMidiManager } from '../core/SessionMidiController';
import { useMidiDevices } from '../hooks/useMidiDevices';
import BassGeneratorControls from './BassGeneratorControls';
import GeneratorControls from './GeneratorControls';
import MidiConfiguration from './MidiConfiguration';
import ProjectManager from './ProjectManager';
import './CreaLab.css';
import { GeneratorEngine } from '../core/GeneratorEngine';
import { MODULE_KNOB_LABELS, EURORACK_MODULES } from '../data/EurorackModules';

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
  inputDevice: '',
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
  const { inputDevices, outputDevices } = useMidiDevices();
  const [showMidiConfig, setShowMidiConfig] = useState(false);
  const [showProjectManager, setShowProjectManager] = useState(false);
  const [midiMapping, setMidiMapping] = useState(false);
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

  useEffect(() => {
    const stored = localStorage.getItem('crealab_project');
    if (stored) {
      try {
        setProject(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to load project', e);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('crealab_project', JSON.stringify(project));
  }, [project]);

  useEffect(() => {
    const manager = SessionMidiManager.getInstance();
    project.tracks.forEach(track => {
      manager.mapTrackToStrip(track.trackNumber, track.id);
    });
  }, [project.tracks]);

  useEffect(() => {
    GeneratorEngine.getInstance().updateTracks(project.tracks);
  }, [project.tracks]);

  useEffect(() => {
    const engine = GeneratorEngine.getInstance();
    if (project.transport.isPlaying) {
      engine.start(project.tracks, project.globalTempo, project.key, project.scale);
    } else {
      engine.stop();
    }
  }, [project.transport.isPlaying, project.globalTempo, project.key, project.scale, project.tracks]);

  useEffect(() => {
    if (!controller) return;
    setProject(prev => {
      const newTracks = prev.tracks.map(t => {
        const strip = controller.channelStrips[t.trackNumber - 1];
        if (!strip) return t;
        return {
          ...t,
          controls: {
            ...t.controls,
            intensity: strip.values.fader,
            paramA: strip.values.knob1,
            paramB: strip.values.knob2,
            paramC: strip.values.knob3,
            playStop: strip.values.button1,
            mode: strip.values.button2 ? 1 : 0
          }
        };
      }) as any;
      const engine = GeneratorEngine.getInstance();
      newTracks.forEach(t => engine.updateTrackParameters(t));
      return { ...prev, tracks: newTracks };
    });
  }, [controller]);

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

  const updateVisualLayer = (trackNumber: number, layer: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, visualLayer: layer || undefined }
          : t
      ) as any
    }));
  };

  const updateVisualPad = (trackNumber: number, pad: number) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber ? { ...t, visualPad: pad } : t
      ) as any
    }));
  };

  const updateInputDevice = (trackNumber: number, deviceId: string) => {
    const device = inputDevices.find(d => d.id === deviceId);
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, inputDevice: deviceId, inputDeviceName: device?.name || '' }
          : t
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
    setProject(prev => {
      const newTracks = prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, controls: { ...t.controls, ...changes } }
          : t
      ) as any;
      const engine = GeneratorEngine.getInstance();
      const track = newTracks[trackNumber - 1];
      engine.updateTrackParameters(track);
      return { ...prev, tracks: newTracks };
    });
  };

  const updateGeneratorParameters = (
    trackNumber: number,
    params: Record<string, any>
  ) => {
    setProject(prev => {
      const newTracks = prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? { ...t, generator: { ...t.generator, parameters: params } }
          : t
      ) as any;
      const engine = GeneratorEngine.getInstance();
      engine.updateTrackParameters(newTracks[trackNumber - 1]);
      return { ...prev, tracks: newTracks };
    });
  };

  const updateGeneratorType = (trackNumber: number, type: string) => {
    setProject(prev => {
      const newTracks = prev.tracks.map(t =>
        t.trackNumber === trackNumber
          ? {
              ...t,
              generator: {
                ...t.generator,
                type: type as any,
                enabled: type !== 'off'
              },
              controls: {
                ...t.controls,
                playStop: type !== 'off' || t.controls.playStop
              }
            }
          : t
      ) as any;
      const engine = GeneratorEngine.getInstance();
      engine.changeGeneratorType(newTracks[trackNumber - 1], type as GeneratorType);
      return { ...prev, tracks: newTracks };
    });
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
        onOpenMidiConfig={() => setShowMidiConfig(true)}
        onOpenProjectManager={() => setShowProjectManager(true)}
        isPlaying={project.transport.isPlaying}
        onPlayToggle={() =>
          setProject(p => ({
            ...p,
            transport: { ...p.transport, isPlaying: !p.transport.isPlaying }
          }))
        }
        isMidiMapping={midiMapping}
        onToggleMidiMapping={() => setMidiMapping(m => !m)}
      />
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
                  className="device-selector"
                  value={track.inputDevice || ''}
                  onChange={e => updateInputDevice(track.trackNumber, e.target.value)}
                >
                  <option value="">MIDI Input</option>
                  {inputDevices.map(dev => (
                    <option key={dev.id} value={dev.id}>{dev.name}</option>
                  ))}
                </select>

                <div className="output-row">
                  <select
                    className="device-selector"
                    value={track.outputDevice}
                    onChange={e => updateOutputDevice(track.trackNumber, e.target.value)}
                  >
                    <option value="">MIDI Output</option>
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

                <div className="visual-row">
                  <select
                    className="device-selector"
                    value={track.visualLayer || ''}
                    onChange={e =>
                      updateVisualLayer(track.trackNumber, e.target.value)
                    }
                  >
                    <option value="">Visual Layer</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                  </select>
                  <input
                    className="channel-selector"
                    type="number"
                    min={0}
                    max={127}
                    value={track.visualPad ?? ''}
                    onChange={e =>
                      updateVisualPad(
                        track.trackNumber,
                        parseInt(e.target.value) || 0
                      )
                    }
                    placeholder="Pad note"
                  />
                </div>

                <div className="section-divider" />
                <div className="section-title">Controles MIDI</div>
                <LaunchControlStrip
                  strip={controller?.channelStrips[track.trackNumber - 1] || null}
                  labels={MODULE_KNOB_LABELS[track.trackType]}
                />

                <div className="section-divider" />
                <div className="section-title">Generador</div>
                <select
                  className="track-type-selector"
                  value={track.trackType}
                  onChange={e =>
                    updateTrackType(track.trackNumber, e.target.value as TrackType)
                  }
                >
                  {EURORACK_MODULES.map(m => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>

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

                <GeneratorControls
                  track={track}
                  onChange={changes => updateTrackControls(track.trackNumber, changes)}
                  mappingMode={midiMapping}
                />

                {track.trackType === 'bass' && (
                  <BassGeneratorControls
                    track={track}
                    onParametersChange={params =>
                      updateGeneratorParameters(track.trackNumber, params)
                    }
                  />
                )}
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

