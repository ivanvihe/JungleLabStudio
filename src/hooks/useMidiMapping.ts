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
  const [inputs, setInputs] = useState<MIDIInput[]>([]);
  const [selectedInputId, setSelectedInputId] = useState<string | null>(null);
  const midiAccessRef = useRef<MIDIAccess | null>(null);

  useEffect(() => {
    return () => {
      midiAccessRef.current?.inputs.forEach((input) => (input.onmidimessage = null));
    };
  }, []);

  const applyHandlerToInputs = (handler: (event: MIDIMessageEvent) => void) => {
    if (!midiAccessRef.current) return;
    midiAccessRef.current.inputs.forEach((input) => {
      input.onmidimessage = !selectedInputId || input.id === selectedInputId ? handler : null;
    });
  };

  const refreshInputs = (access: MIDIAccess) => {
    const availableInputs = Array.from(access.inputs.values());
    setInputs(availableInputs);
    if (!selectedInputId && availableInputs.length) {
      setSelectedInputId(availableInputs[0].id);
    }
  };

  const handleMessage = (parameterKey: string | null) => (event: MIDIMessageEvent) => {
    const data = event.data;
    if (!data || data.length < 3) return;
    const [statusByte, control, value] = data;
    const command = statusByte & 0xf0;
    if (command !== 0xb0) return; // solo CC
    const channel = statusByte & 0x0f;

    if (parameterKey) {
      const mapping = { control, channel } satisfies MidiMapping;
      mappingsRef.current = { ...mappingsRef.current, [parameterKey]: mapping };
      setMappings(mappingsRef.current);
      setLearning(null);
      setStatus(`Asignado CC${control} ch${channel}`);
      applyHandlerToInputs(handleMessage(null));
      return;
    }

    Object.entries(mappingsRef.current).forEach(([key, mapping]) => {
      if (mapping.control === control && mapping.channel === channel) {
        onValue(key, value / 127);
      }
    });
  };

  const start = async () => {
    try {
      const access = await navigator.requestMIDIAccess();
      midiAccessRef.current = access;
      refreshInputs(access);
      applyHandlerToInputs(handleMessage(null));
      access.onstatechange = () => {
        refreshInputs(access);
        applyHandlerToInputs(handleMessage(null));
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
    applyHandlerToInputs(handleMessage(parameterKey));
  };

  const stopLearning = () => {
    setLearning(null);
    if (!midiAccessRef.current) return;
    applyHandlerToInputs(handleMessage(null));
  };

  const selectInput = (id: string) => {
    setSelectedInputId(id);
    if (!midiAccessRef.current) return;
    applyHandlerToInputs(handleMessage(learning));
    const name = midiAccessRef.current.inputs.get(id)?.name ?? 'MIDI';
    setStatus(`Escuchando ${name}`);
  };

  return {
    mappings,
    learning,
    enabled,
    status,
    inputs,
    selectedInputId,
    start,
    learn,
    stopLearning,
    selectInput,
  } as const;
};
