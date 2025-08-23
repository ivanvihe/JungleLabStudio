import { useEffect, useState, useCallback } from 'react';
import { MidiDevice } from '../types/CrealabTypes';
import { MidiManager } from '../core/MidiManager';
import { MidiClockState } from '../core/MidiClock';

interface UseMidiDevicesReturn {
  inputDevices: MidiDevice[];
  outputDevices: MidiDevice[];
  midiClock: MidiClockState;
  isInitialized: boolean;
  testDevice: (deviceId: string) => Promise<boolean>;
  refreshDevices: () => void;
  sendNote: (deviceId: string, channel: number, note: number, velocity: number, duration?: number) => Promise<boolean>;
  sendCC: (deviceId: string, channel: number, controller: number, value: number) => Promise<boolean>;
}

export const useMidiDevices = (): UseMidiDevicesReturn => {
  const [inputDevices, setInputDevices] = useState<MidiDevice[]>([]);
  const [outputDevices, setOutputDevices] = useState<MidiDevice[]>([]);
  const [midiClock, setMidiClock] = useState<MidiClockState>({
    isRunning: false,
    bpm: 120,
    currentBeat: 0,
    currentStep: 0,
    source: 'internal'
  });
  const [isInitialized, setIsInitialized] = useState(false);

  const midiManager = MidiManager.getInstance();

  const refreshDevices = useCallback(() => {
    setInputDevices(midiManager.getInputDevices());
    setOutputDevices(midiManager.getOutputDevices());
  }, [midiManager]);

  useEffect(() => {
    const initializeMidi = async () => {
      await midiManager.initialize();
      refreshDevices();
      setIsInitialized(true);
    };

    initializeMidi();

    const clockListener = (state: MidiClockState) => {
      setMidiClock(state);
    };
    midiManager.getMidiClock().addListener(clockListener);

    const handleDeviceChange = () => {
      refreshDevices();
    };
    window.addEventListener('midiDeviceChange', handleDeviceChange);

    return () => {
      midiManager.getMidiClock().removeListener(clockListener);
      window.removeEventListener('midiDeviceChange', handleDeviceChange);
    };
  }, [midiManager, refreshDevices]);

  const testDevice = useCallback(async (deviceId: string): Promise<boolean> => {
    return midiManager.testDevice(deviceId);
  }, [midiManager]);

  const sendNote = useCallback(async (
    deviceId: string,
    channel: number,
    note: number,
    velocity: number,
    duration: number = 100
  ): Promise<boolean> => {
    return midiManager.sendNote(deviceId, channel, note, velocity, duration);
  }, [midiManager]);

  const sendCC = useCallback(async (
    deviceId: string,
    channel: number,
    controller: number,
    value: number
  ): Promise<boolean> => {
    return midiManager.sendCC(deviceId, channel, controller, value);
  }, [midiManager]);

  return {
    inputDevices,
    outputDevices,
    midiClock,
    isInitialized,
    testDevice,
    refreshDevices,
    sendNote,
    sendCC
  };
};

