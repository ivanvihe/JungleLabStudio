import { useState, useEffect, useRef } from 'react';
import { AudioVisualizerEngine } from '../core/AudioVisualizerEngine';
import { LoadedPreset } from '../core/PresetLoader';

interface MidiTrigger { layerId: string; presetId: string; velocity: number }
interface LayerEffect { effect: string; alwaysOn: boolean; active: boolean }

interface MidiOptions {
  isFullscreenMode: boolean;
  availablePresets: LoadedPreset[];
  layerChannels: Record<string, number>;
  layerEffects: Record<string, LayerEffect>;
  setLayerEffects: React.Dispatch<React.SetStateAction<Record<string, LayerEffect>>>;
  effectMidiNotes: Record<string, number>;
  launchpadChannel: number;
  launchpadNote: number;
  onLaunchpadToggle: () => void;
  engineRef: React.MutableRefObject<AudioVisualizerEngine | null>;
}

export function useMidi(options: MidiOptions) {
  const {
    isFullscreenMode,
    availablePresets,
    layerChannels,
    layerEffects,
    setLayerEffects,
    effectMidiNotes,
    launchpadChannel,
    launchpadNote,
    onLaunchpadToggle,
    engineRef
  } = options;

  const tickCountRef = useRef(0);
  const lastBeatRef = useRef<number | null>(null);
  const bpmSamplesRef = useRef<number[]>([]);

  const [midiDevices, setMidiDevices] = useState<any[]>([]);
  const [midiDeviceId, setMidiDeviceId] = useState<string | null>(null);
  const [midiActive, setMidiActive] = useState(false);
  const [bpm, setBpm] = useState<number | null>(null);
  const [beatActive, setBeatActive] = useState(false);
  const [midiTrigger, setMidiTrigger] = useState<MidiTrigger | null>(null);
  const [midiClockDelay, setMidiClockDelay] = useState(() => parseInt(localStorage.getItem('midiClockDelay') || '0'));
  const [midiClockType, setMidiClockType] = useState(() => localStorage.getItem('midiClockType') || 'midi');

  useEffect(() => {
    if (isFullscreenMode) return;

    const handleMIDIMessage = (event: any) => {
      setMidiActive(true);
      setTimeout(() => setMidiActive(false), 100);
      const [statusByte, note, vel] = event.data;

      if (statusByte === 0xfa || statusByte === 0xfb || statusByte === 0xfc) {
        tickCountRef.current = 0;
        lastBeatRef.current = null;
        bpmSamplesRef.current = [];
        if (statusByte === 0xfc) {
          setBpm(null);
        }
        return;
      }

      if (statusByte === 0xf8 && midiClockType === 'midi') {
        const now = performance.now();
        tickCountRef.current++;
        if (tickCountRef.current >= 24) {
          const lastBeat = lastBeatRef.current;
          if (lastBeat !== null) {
            const diff = now - lastBeat;
            const bpmVal = 60000 / diff;
            if (isFinite(bpmVal)) {
              bpmSamplesRef.current.push(bpmVal);
              if (bpmSamplesRef.current.length > 8) bpmSamplesRef.current.shift();
              const avg = bpmSamplesRef.current.reduce((a, b) => a + b, 0) / bpmSamplesRef.current.length;
              setBpm(avg);
              if (engineRef.current) {
                engineRef.current.updateBpm(avg);
              }
            }
          }
          lastBeatRef.current = now;
          tickCountRef.current = 0;

          const trigger = () => {
            setBeatActive(true);
            setTimeout(() => setBeatActive(false), 100);
            if (engineRef.current) {
              engineRef.current.triggerBeat();
            }
          };

          if (midiClockDelay > 0) {
            setTimeout(trigger, midiClockDelay);
          } else {
            trigger();
          }
        }
        return;
      }

      const command = statusByte & 0xf0;
      const channel = (statusByte & 0x0f) + 1;
      if (command === 0x90 && vel > 0 && channel === launchpadChannel && note === launchpadNote) {
        onLaunchpadToggle();
        return;
      }
      const channelToLayer = Object.fromEntries(
        Object.entries(layerChannels).map(([layerId, ch]) => [ch, layerId])
      ) as Record<number, string>;
      const layerId = channelToLayer[channel];

      const matchedEffect = Object.entries(effectMidiNotes).find(([, n]) => n === note)?.[0];

      if (command === 0x90 && vel > 0) {
        if (matchedEffect) {
          setLayerEffects(prev => {
            const updated = { ...prev };
            Object.keys(prev).forEach(id => {
              if (prev[id].effect === matchedEffect && !prev[id].alwaysOn) {
                updated[id] = { ...prev[id], active: true };
              }
            });
            return updated;
          });
        }
        const preset = availablePresets.find(p => p.config.note === note);
        if (layerId && preset) {
          setMidiTrigger({ layerId, presetId: preset.id, velocity: vel });
        }
      } else if (command === 0x80 || (command === 0x90 && vel === 0)) {
        if (matchedEffect) {
          setLayerEffects(prev => {
            const updated = { ...prev };
            Object.keys(prev).forEach(id => {
              if (prev[id].effect === matchedEffect && !prev[id].alwaysOn) {
                updated[id] = { ...prev[id], active: false };
              }
            });
            return updated;
          });
        }
      }
    };

    if ((navigator as any).requestMIDIAccess) {
      (navigator as any).requestMIDIAccess({ sysex: true })
        .then((access: any) => {
          const inputs = Array.from(access.inputs.values());
          setMidiDevices(inputs);

          inputs.forEach((input: any) => {
            if (!midiDeviceId || input.id === midiDeviceId) {
              input.onmidimessage = handleMIDIMessage;
            } else {
              input.onmidimessage = null;
            }
          });

          access.onstatechange = () => {
            const ins = Array.from(access.inputs.values());
            setMidiDevices(ins);
            ins.forEach((input: any) => {
              if (!midiDeviceId || input.id === midiDeviceId) {
                input.onmidimessage = handleMIDIMessage;
              } else {
                input.onmidimessage = null;
              }
            });
          };
        })
        .catch((err: any) => console.warn('MIDI access error', err));
    }
  }, [midiDeviceId, midiClockType, midiClockDelay, layerChannels, layerEffects, availablePresets, isFullscreenMode, launchpadChannel, launchpadNote, effectMidiNotes, onLaunchpadToggle, engineRef]);

  return {
    midiDevices,
    midiDeviceId,
    setMidiDeviceId,
    midiActive,
    bpm,
    beatActive,
    midiTrigger,
    setMidiTrigger,
    midiClockDelay,
    setMidiClockDelay,
    midiClockType,
    setMidiClockType,
  };
}

