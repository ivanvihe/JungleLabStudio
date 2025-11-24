import { useEffect, useRef, useState } from 'react';
import { MidiMapping } from '../types';

interface MidiHookOptions {
  onValue: (parameterKey: string, normalizedValue: number) => void;
}

export const useMidiMapping = ({ onValue }: MidiHookOptions) => {
  const mappingsRef = useRef<Record<string, MidiMapping>>({});
  const [mappings, setMappings] = useState<Record<string, MidiMapping>>({});
  const [learning, setLearning] = useState<string | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [status, setStatus] = useState('MIDI inactivo');
  const midiAccessRef = useRef<WebMidi.MIDIAccess | null>(null);

  useEffect(() => {
    return () => {
      midiAccessRef.current?.inputs.forEach((input) => (input.onmidimessage = null));
    };
  }, []);

  const handleMessage = (parameterKey: string | null) => (event: WebMidi.MIDIMessageEvent) => {
    const [statusByte, control, value] = event.data;
    const command = statusByte & 0xf0;
    if (command !== 0xb0) return; // solo CC
    const channel = statusByte & 0x0f;

    if (parameterKey) {
      const mapping = { control, channel } satisfies MidiMapping;
      mappingsRef.current = { ...mappingsRef.current, [parameterKey]: mapping };
      setMappings(mappingsRef.current);
      setLearning(null);
      setStatus(`Asignado CC${control} ch${channel}`);
      midiAccessRef.current?.inputs.forEach((input) => {
        input.onmidimessage = handleMessage(null);
      });
      return;
    }

    Object.entries(mappingsRef.current).forEach(([key, mapping]) => {
      if (mapping.control === control && mapping.channel === channel) {
        onValue(key, value / 127);
      }
    });
  };

  const start = async () => {
    if (enabled) return;
    try {
      const access = await navigator.requestMIDIAccess();
      midiAccessRef.current = access;
      access.inputs.forEach((input) => {
        input.onmidimessage = handleMessage(null);
      });
      access.onstatechange = () => {
        access.inputs.forEach((input) => {
          input.onmidimessage = handleMessage(null);
        });
      };
      setEnabled(true);
      setStatus('Escuchando MIDI');
    } catch (err) {
      console.error(err);
      setStatus('Error al abrir MIDI');
    }
  };

  const learn = (parameterKey: string) => {
    setLearning(parameterKey);
    if (!midiAccessRef.current) return;
    midiAccessRef.current.inputs.forEach((input) => {
      input.onmidimessage = handleMessage(parameterKey);
    });
  };

  const stopLearning = () => {
    setLearning(null);
    if (!midiAccessRef.current) return;
    midiAccessRef.current.inputs.forEach((input) => {
      input.onmidimessage = handleMessage(null);
    });
  };

  return { mappings, learning, enabled, status, start, learn, stopLearning } as const;
};
