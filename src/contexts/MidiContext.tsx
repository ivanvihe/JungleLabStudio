
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
  });

  const value = {
    ...midiData,
    startMidiLearn,
    cancelMidiLearn,
    midiLearnTarget,
    lastCapturedNote,
  };

  return <MidiContext.Provider value={value}>{children}</MidiContext.Provider>;
};
