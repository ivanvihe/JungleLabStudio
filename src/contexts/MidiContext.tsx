
import React, { createContext, useContext, useState, useCallback } from 'react';
import { useMidi } from '../hooks/useMidi';
import { AudioVisualizerEngine } from '../core/AudioVisualizerEngine';
import { LoadedPreset } from '../core/PresetLoader';

interface MidiContextType {
  // Original useMidi return values
  midiDevices: any[];
  midiDeviceId: string | null;
  setMidiDeviceId: (id: string | null) => void;
  midiActive: boolean;
  bpm: number | null;
  beatActive: boolean;
  midiTrigger: any | null; // Define a proper type later
  setMidiTrigger: (trigger: any | null) => void;
  midiClockSettings: any; // Define a proper type later
  updateClockSettings: (updates: any) => void; // Define a proper type later
  setInternalBpm: (newBpm: number) => void;
  internalBpm: number;
  clockStable: boolean;
  currentMeasure: number;
  currentBeat: number;


  // MIDI Learn functionality
  startMidiLearn: (target: string) => void;
  cancelMidiLearn: () => void;
  midiLearnTarget: string | null;
  lastCapturedNote: { target: string, note: number } | null;

  // MIDI CC Learn for parameters
  startParameterLearn: (target: string, meta?: MidiLearnMeta) => void;
  cancelParameterLearn: () => void;
  parameterLearnTarget: MidiLearnTarget | null;
  parameterMappings: Record<string, MidiMapping>;
  mappedParameterEvent: MidiMappedEvent | null;
  clearParameterMapping: (target: string) => void;
}

interface MidiMapping {
  cc: number;
  channel: number;
  min?: number;
  max?: number;
  label?: string;
}

interface MidiLearnMeta {
  min?: number;
  max?: number;
  label?: string;
}

interface MidiLearnTarget extends MidiLearnMeta {
  id: string;
}

interface MidiMappedEvent {
  target: string;
  value: number;
}

const MidiContext = createContext<MidiContextType | null>(null);

export const useMidiContext = () => {
  const context = useContext(MidiContext);
  if (!context) {
    throw new Error('useMidiContext must be used within a MidiContextProvider');
  }
  return context;
};

interface MidiContextProviderProps {
  children: React.ReactNode;
  // Props needed for useMidi hook
  isFullscreenMode: boolean;
  availablePresets: LoadedPreset[];
  layerChannels: Record<string, number>;
  layerEffects: Record<string, any>; // Define proper type later
  setLayerEffects: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  effectMidiNotes: Record<string, number>;
  engineRef: React.MutableRefObject<AudioVisualizerEngine | null>;
}

export const MidiContextProvider: React.FC<MidiContextProviderProps> = ({
  children,
  ...midiOptions
}) => {
  const [midiLearnTarget, setMidiLearnTarget] = useState<string | null>(null);
  const [lastCapturedNote, setLastCapturedNote] = useState<{target: string, note: number} | null>(null);
  const [parameterLearnTarget, setParameterLearnTarget] = useState<MidiLearnTarget | null>(null);
  const [parameterMappings, setParameterMappings] = useState<Record<string, MidiMapping>>(() => {
    try {
      const stored = localStorage.getItem('parameterMidiMappings');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });
  const [mappedParameterEvent, setMappedParameterEvent] = useState<MidiMappedEvent | null>(null);

  const startMidiLearn = useCallback((target: string) => {
    setMidiLearnTarget(target);
    setLastCapturedNote(null); // Reset previous capture
  }, []);

  const cancelMidiLearn = useCallback(() => {
    setMidiLearnTarget(null);
  }, []);

  const onNoteLearned = useCallback((note: number) => {
    if (midiLearnTarget) {
      setLastCapturedNote({ target: midiLearnTarget, note });
    }
    setMidiLearnTarget(null); // Stop learning after capture
  }, [midiLearnTarget]);

  const midiData = useMidi({
    ...midiOptions,
    onNoteLearned,
    isLearning: !!midiLearnTarget,
    onControlChange: ({ cc, value, channel }) => {
      if (parameterLearnTarget && midiOptions.isFullscreenMode) return; // avoid mapping while fullscreen prevent accidents
      const match = Object.entries(parameterMappings).find(
        ([, mapping]) => mapping.cc === cc && mapping.channel === channel,
      );
      if (match) {
        const [target, mapping] = match;
        const normalized = value / 127;
        const scaled = mapping.min !== undefined && mapping.max !== undefined
          ? mapping.min + normalized * (mapping.max - mapping.min)
          : normalized;
        setMappedParameterEvent({ target, value: scaled });
      }
    },
    onControlLearned: (cc, channel) => {
      if (parameterLearnTarget) {
        setParameterMappings(prev => {
          const next = { ...prev, [parameterLearnTarget.id]: { cc, channel, min: parameterLearnTarget.min, max: parameterLearnTarget.max, label: parameterLearnTarget.label } };
          localStorage.setItem('parameterMidiMappings', JSON.stringify(next));
          return next;
        });
        setMappedParameterEvent({ target: parameterLearnTarget.id, value: parameterLearnTarget.min ?? 0 });
        setParameterLearnTarget(null);
      }
    },
    isControlLearning: !!parameterLearnTarget,
  });

  const startParameterLearn = useCallback((target: string, meta?: MidiLearnMeta) => {
    setParameterLearnTarget({ id: target, ...meta });
  }, []);

  const cancelParameterLearn = useCallback(() => {
    setParameterLearnTarget(null);
  }, []);

  const clearParameterMapping = useCallback((target: string) => {
    setParameterMappings(prev => {
      const next = { ...prev };
      delete next[target];
      localStorage.setItem('parameterMidiMappings', JSON.stringify(next));
      return next;
    });
  }, []);

  const value = {
    ...midiData,
    startMidiLearn,
    cancelMidiLearn,
    midiLearnTarget,
    lastCapturedNote,
    startParameterLearn,
    cancelParameterLearn,
    parameterLearnTarget,
    parameterMappings,
    mappedParameterEvent,
    clearParameterMapping,
  };

  return <MidiContext.Provider value={value}>{children}</MidiContext.Provider>;
};
