import React, { useEffect, useState } from 'react';
import { CreaLabProject, Track, MidiClip, MidiNote } from '../types/CrealabTypes';
import './CreaLab.css';

interface CreaLabProps {
  onSwitchToAudioVisualizer: () => void;
}

const DEFAULT_SLOTS = 8;

export const CreaLab: React.FC<CreaLabProps> = ({ onSwitchToAudioVisualizer }) => {
  const [midiDevices, setMidiDevices] = useState<{ id: string; name: string }[]>([]);
  const [dragging, setDragging] = useState<{ trackIndex: number; slotIndex: number } | null>(null);

  useEffect(() => {
    const nav = navigator as any;
    if (nav.requestMIDIAccess) {
      nav.requestMIDIAccess().then((access: any) => {
        const inputs = Array.from(access.inputs.values()).map((d: any) => ({
          id: d.id,
          name: d.name || d.id
        }));
        setMidiDevices(inputs);
      }).catch(() => {
        // ignore
      });
    }
  }, []);

  const [project, setProject] = useState<CreaLabProject>({
    id: 'project-1',
    name: 'New Project',
    tracks: [
      {
        id: 'track-1',
        name: 'Track 1',
        midiDevice: '',
        midiChannel: 1,
        clips: Array(DEFAULT_SLOTS).fill(null)
      }
    ],
    globalTempo: 128,
    key: 'C',
    scale: 'minor'
  });

  const addTrack = () => {
    const newTrack: Track = {
      id: `track-${Date.now()}`,
      name: `Track ${project.tracks!.length + 1}`,
      midiDevice: '',
      midiChannel: 1,
      clips: Array(DEFAULT_SLOTS).fill(null)
    };
    setProject(prev => ({
      ...prev,
      tracks: [...(prev.tracks || []), newTrack]
    }));
  };

  const renameTrack = (trackId: string, name: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks?.map(t => (t.id === trackId ? { ...t, name } : t))
    }));
  };

  const assignMidiDevice = (trackId: string, device: string) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks?.map(t => (t.id === trackId ? { ...t, midiDevice: device } : t))
    }));
  };

  const assignMidiChannel = (trackId: string, channel: number) => {
    setProject(prev => ({
      ...prev,
      tracks: prev.tracks?.map(t => (t.id === trackId ? { ...t, midiChannel: channel } : t))
    }));
  };

  const createMidiClip = (trackIndex: number, slotIndex: number) => {
    const track = project.tracks?.[trackIndex];
    if (!track) return;

    // Generar algunas notas de ejemplo basadas en la escala del proyecto
    const scaleNotes = getScaleNotes(project.key, project.scale);
    const randomNotes: MidiNote[] = [];

    // Crear un patrón básico de 4 beats
    for (let i = 0; i < 4; i++) {
      if (Math.random() > 0.5) {
        // 50% probabilidad por beat
        randomNotes.push({
          note: scaleNotes[Math.floor(Math.random() * scaleNotes.length)],
          time: i,
          velocity: 80 + Math.floor(Math.random() * 47), // 80-127
          duration: 0.25 + Math.random() * 0.75 // 0.25-1 beats
        });
      }
    }

    const newClip: MidiClip = {
      id: `clip-${Date.now()}`,
      name: `Clip ${slotIndex + 1}`,
      trackType: 'lead', // Por defecto
      notes: randomNotes,
      duration: 4, // 4 beats
      channel: track.midiChannel,
      enabled: true
    };

    setProject(prev => ({
      ...prev,
      tracks: prev.tracks?.map((t, idx) =>
        idx === trackIndex
          ? {
              ...t,
              clips: t.clips.map((c, cidx) => (cidx === slotIndex ? newClip : c))
            }
          : t
      )
    }));

    // Enviar notas MIDI si hay dispositivo configurado
    sendMidiClip(newClip, track.midiDevice);
  };

  const handleDragStart = (trackIndex: number, slotIndex: number) => {
    setDragging({ trackIndex, slotIndex });
  };

  const handleDrop = (toTrackIndex: number, toSlotIndex: number) => {
    if (!dragging) return;
    setProject(prev => {
      const tracks = prev.tracks?.map(t => ({ ...t, clips: [...t.clips] })) || [];
      const clip = tracks[dragging.trackIndex].clips[dragging.slotIndex];
      tracks[dragging.trackIndex].clips[dragging.slotIndex] = tracks[toTrackIndex].clips[toSlotIndex];
      tracks[toTrackIndex].clips[toSlotIndex] = clip;
      return { ...prev, tracks };
    });
    setDragging(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const getScaleNotes = (key: string, scale: string): number[] => {
    const keyToRoot: { [key: string]: number } = {
      C: 60,
      'C#': 61,
      D: 62,
      'D#': 63,
      E: 64,
      F: 65,
      'F#': 66,
      G: 67,
      'G#': 68,
      A: 69,
      'A#': 70,
      B: 71
    };

    const scaleIntervals: { [scale: string]: number[] } = {
      minor: [0, 2, 3, 5, 7, 8, 10],
      major: [0, 2, 4, 5, 7, 9, 11],
      dorian: [0, 2, 3, 5, 7, 9, 10],
      pentatonic: [0, 2, 5, 7, 9]
    };

    const root = keyToRoot[key] || 60;
    const intervals = scaleIntervals[scale] || scaleIntervals['minor'];

    return intervals.map(interval => root + interval);
  };

  const sendMidiClip = async (clip: MidiClip, deviceId: string) => {
    if (!deviceId) return;

    try {
      const access = await (navigator as any).requestMIDIAccess();
      const output = access.outputs.get(deviceId);
      if (!output) return;

      // Reproducir las notas del clip
      clip.notes.forEach((note, index) => {
        setTimeout(() => {
          // Note On
          output.send([0x90 + (clip.channel - 1), note.note, note.velocity]);

          // Note Off después de la duración
          setTimeout(() => {
            output.send([0x80 + (clip.channel - 1), note.note, 0]);
          }, note.duration * 500); // Convertir beats a ms (asumiendo 120 BPM)
        }, note.time * 500);
      });
    } catch (error) {
      console.log('No se pudo enviar MIDI:', error);
    }
  };

  return (
    <div className="crealab-container">
      <header className="crealab-header">
        <div className="crealab-title">
          <h1>🎼 Crea Lab</h1>
          <span className="project-name">{project.name}</span>
        </div>

        <div className="crealab-controls">
          <div className="global-settings">
            <label>
              BPM:
              <input
                type="number"
                value={project.globalTempo}
                onChange={(e) =>
                  setProject(prev => ({
                    ...prev,
                    globalTempo: parseInt(e.target.value) || 128
                  }))
                }
                min={60}
                max={200}
              />
            </label>
            <label>
              Key:
              <select
                value={project.key}
                onChange={(e) => setProject(prev => ({ ...prev, key: e.target.value }))}
              >
                {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].map(key => (
                  <option key={key} value={key}>{key}</option>
                ))}
              </select>
            </label>
          </div>

          <button onClick={onSwitchToAudioVisualizer} className="switch-app-btn">
            🎨 AudioVisualizer
          </button>
        </div>
      </header>

      <main className="crealab-workspace">
        <div className="track-view">
          {project.tracks?.map((track, trackIndex) => (
            <div key={track.id} className="track-column">
              <div className="track-header">
                <input
                  value={track.name}
                  onChange={(e) => renameTrack(track.id, e.target.value)}
                />
                <select
                  value={track.midiDevice}
                  onChange={(e) => assignMidiDevice(track.id, e.target.value)}
                >
                  <option value="">Select MIDI</option>
                  {midiDevices.map(dev => (
                    <option key={dev.id} value={dev.id}>{dev.name}</option>
                  ))}
                </select>
                <select
                  value={track.midiChannel}
                  onChange={(e) => assignMidiChannel(track.id, parseInt(e.target.value))}
                >
                  {Array.from({ length: 16 }, (_, i) => i + 1).map(ch => (
                    <option key={ch} value={ch}>Ch {ch}</option>
                  ))}
                </select>
              </div>
              {track.clips.map((clip, slotIndex) => (
                <div
                  key={slotIndex}
                  className="clip-slot"
                  draggable={!!clip}
                  onDragStart={() => handleDragStart(trackIndex, slotIndex)}
                  onDragOver={handleDragOver}
                  onDrop={() => handleDrop(trackIndex, slotIndex)}
                  onDoubleClick={() => createMidiClip(trackIndex, slotIndex)}
                >
                  {clip?.name || ''}
                </div>
              ))}
            </div>
          ))}
          <div className="add-track-button">
            <button onClick={addTrack}>+</button>
          </div>
        </div>
      </main>
    </div>
  );
};
