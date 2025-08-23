export interface MidiClockState {
  isRunning: boolean;
  bpm: number;
  currentBeat: number;
  currentStep: number;
  source: 'internal' | 'external';
}

type MidiClockListener = (state: MidiClockState) => void;

export class MidiClock {
  private state: MidiClockState = {
    isRunning: false,
    bpm: 120,
    currentBeat: 0,
    currentStep: 0,
    source: 'internal'
  };
  private listeners: Set<MidiClockListener> = new Set();
  private intervalId: any = null;

  start(bpm?: number) {
    if (bpm) this.state.bpm = bpm;
    if (this.state.isRunning) return;
    this.state.isRunning = true;
    const interval = (60 / this.state.bpm / 24) * 1000; // 24 PPQN
    this.intervalId = setInterval(() => this.tick(), interval);
    this.emit();
  }

  stop() {
    this.state.isRunning = false;
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = null;
    this.emit();
  }

  private tick() {
    if (!this.state.isRunning) return;
    this.state.currentStep++;
    if (this.state.currentStep % 24 === 0) {
      this.state.currentBeat++;
    }
    this.emit();
  }

  setSource(source: 'internal' | 'external') {
    this.state.source = source;
    this.emit();
  }

  receiveClock() {
    if (this.state.source !== 'external') return;
    this.tick();
  }

  receiveStart() {
    if (this.state.source !== 'external') return;
    this.state.isRunning = true;
    this.state.currentBeat = 0;
    this.state.currentStep = 0;
    this.emit();
  }

  receiveContinue() {
    if (this.state.source !== 'external') return;
    this.state.isRunning = true;
    this.emit();
  }

  receiveStop() {
    if (this.state.source !== 'external') return;
    this.state.isRunning = false;
    this.emit();
  }

  addListener(cb: MidiClockListener) {
    this.listeners.add(cb);
  }

  removeListener(cb: MidiClockListener) {
    this.listeners.delete(cb);
  }

  private emit() {
    const snapshot: MidiClockState = { ...this.state };
    this.listeners.forEach(l => l(snapshot));
  }

  getState(): MidiClockState {
    return { ...this.state };
  }
}
