import { MidiDevice, MidiMessage, MidiNote } from '../types/CrealabTypes';
import { MidiClock } from './MidiClock';

export interface MidiConnectionStatus {
  connected: boolean;
  lastActivity: number;
  messageCount: number;
}

export class MidiManager {
  private static instance: MidiManager;
  private midiAccess: any = null;
  private inputDevices: Map<string, MidiDevice> = new Map();
  private outputDevices: Map<string, MidiDevice> = new Map();
  private connectionStatus: Map<string, MidiConnectionStatus> = new Map();
  private messageListeners: Map<string, (message: MidiMessage) => void> = new Map();
  private midiClock: MidiClock;

  static getInstance(): MidiManager {
    if (!this.instance) {
      this.instance = new MidiManager();
    }
    return this.instance;
  }

  private constructor() {
    this.midiClock = new MidiClock();
    this.initialize();
  }

  async initialize() {
    if (this.midiAccess) return;
    try {
      this.midiAccess = await (navigator as any).requestMIDIAccess({ sysex: true });
      this.midiAccess.onstatechange = this.handleStateChange.bind(this);
      this.scanDevices();
      console.log('MIDI Manager initialized');
    } catch (error) {
      console.error('Failed to initialize MIDI Manager:', error);
    }
  }

  private scanDevices() {
    if (!this.midiAccess) return;

    this.inputDevices.clear();
    for (const input of this.midiAccess.inputs.values()) {
      const device: MidiDevice = {
        id: input.id,
        name: input.name || 'Unknown Input',
        manufacturer: input.manufacturer || '',
        type: 'input',
        state: input.state,
        connection: input.connection
      };
      this.inputDevices.set(input.id, device);
      this.setupInputListener(input);
      this.connectionStatus.set(input.id, {
        connected: input.state === 'connected',
        lastActivity: 0,
        messageCount: 0
      });
    }

    this.outputDevices.clear();
    for (const output of this.midiAccess.outputs.values()) {
      const device: MidiDevice = {
        id: output.id,
        name: output.name || 'Unknown Output',
        manufacturer: output.manufacturer || '',
        type: 'output',
        state: output.state,
        connection: output.connection
      };
      this.outputDevices.set(output.id, device);
      this.connectionStatus.set(output.id, {
        connected: output.state === 'connected',
        lastActivity: 0,
        messageCount: 0
      });
    }
  }

  refreshDevices() {
    this.scanDevices();
  }

  private setupInputListener(input: any) {
    input.onmidimessage = (event: any) => {
      const message: MidiMessage = {
        data: event.data,
        timestamp: event.timeStamp,
        deviceId: input.id
      };
      this.handleMidiMessage(message);
      const status = this.connectionStatus.get(input.id);
      if (status) {
        status.lastActivity = Date.now();
        status.messageCount++;
      }
    };
  }

  private handleMidiMessage(message: MidiMessage) {
    const [status, , data2] = message.data;
    if ((status & 0xf0) === 0x90 && data2 > 0) {
      this.notifyMessage('noteOn', message);
    } else if ((status & 0xf0) === 0x80 || ((status & 0xf0) === 0x90 && data2 === 0)) {
      this.notifyMessage('noteOff', message);
    } else if ((status & 0xf0) === 0xb0) {
      this.notifyMessage('controlChange', message);
    } else if (status === 0xf8) {
      this.midiClock.receiveClock();
    } else if (status === 0xfa) {
      this.midiClock.receiveStart();
    } else if (status === 0xfb) {
      this.midiClock.receiveContinue();
    } else if (status === 0xfc) {
      this.midiClock.receiveStop();
    }
  }

  private notifyMessage(type: string, message: MidiMessage) {
    Array.from(this.messageListeners.values()).forEach(cb => {
      try {
        cb(message);
      } catch (err) {
        console.warn('Error in MIDI message listener', err);
      }
    });
    window.dispatchEvent(new CustomEvent('midiMessage', { detail: { type, message } }));
  }

  private handleStateChange(event: any) {
    this.scanDevices();
    window.dispatchEvent(new CustomEvent('midiDeviceChange', {
      detail: { device: event.port, state: event.port.state }
    }));
  }

  async sendNote(
    deviceId: string,
    channel: number,
    note: number,
    velocity: number,
    duration: number = 100
  ): Promise<boolean> {
    const output = this.midiAccess?.outputs.get(deviceId);
    if (!output) return false;
    try {
      const noteOn = [0x90 + (channel - 1), note, velocity];
      const noteOff = [0x80 + (channel - 1), note, 0];
      output.send(noteOn);
      if (duration > 0) {
        setTimeout(() => output.send(noteOff), duration);
      }
      const status = this.connectionStatus.get(deviceId);
      if (status) {
        status.lastActivity = Date.now();
        status.messageCount++;
      }
      return true;
    } catch (err) {
      console.error('Failed to send MIDI note', err);
      return false;
    }
  }

  async sendCC(
    deviceId: string,
    channel: number,
    controller: number,
    value: number
  ): Promise<boolean> {
    const output = this.midiAccess?.outputs.get(deviceId);
    if (!output) return false;
    try {
      const message = [0xb0 + (channel - 1), controller, value];
      output.send(message);
      const status = this.connectionStatus.get(deviceId);
      if (status) {
        status.lastActivity = Date.now();
        status.messageCount++;
      }
      return true;
    } catch (err) {
      console.error('Failed to send MIDI CC', err);
      return false;
    }
  }

  async sendChord(
    deviceId: string,
    channel: number,
    notes: MidiNote[]
  ): Promise<boolean> {
    const results = await Promise.all(
      notes.map(n => this.sendNote(deviceId, channel, n.note, n.velocity, n.duration * 1000))
    );
    return results.every(Boolean);
  }

  addMessageListener(id: string, callback: (message: MidiMessage) => void) {
    this.messageListeners.set(id, callback);
  }

  removeMessageListener(id: string) {
    this.messageListeners.delete(id);
  }

  getInputDevices(): MidiDevice[] {
    return Array.from(this.inputDevices.values());
  }

  getOutputDevices(): MidiDevice[] {
    return Array.from(this.outputDevices.values());
  }

  getDeviceById(id: string): MidiDevice | undefined {
    return this.inputDevices.get(id) || this.outputDevices.get(id);
  }

  testDevice(deviceId: string): Promise<boolean> {
    return this.sendNote(deviceId, 1, 60, 100, 200);
  }

  getMidiClock(): MidiClock {
    return this.midiClock;
  }
}
