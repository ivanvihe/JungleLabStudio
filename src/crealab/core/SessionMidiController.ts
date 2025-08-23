import { SessionMidiController, ChannelStrip } from '../types/GeneratorTypes';

export class SessionMidiManager {
  private static instance: SessionMidiManager;
  private midiAccess: any = null;
  private activeController: SessionMidiController | null = null;
  private trackMapping: Map<number, string> = new Map(); // strip -> trackId
  private listeners: Array<(ctrl: SessionMidiController) => void> = [];
  
  static getInstance(): SessionMidiManager {
    if (!this.instance) {
      this.instance = new SessionMidiManager();
    }
    return this.instance;
  }
  
  async initialize() {
    try {
      this.midiAccess = await (navigator as any).requestMIDIAccess();
      this.setupMidiListeners();
      console.log('🎛️ Session MIDI Manager initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Session MIDI:', error);
    }
  }
  
  // Detectar y configurar Launch Control XL
  detectLaunchControlXL(): SessionMidiController | null {
    if (!this.midiAccess) return null;
    
    const inputs = Array.from(this.midiAccess.inputs.values());
    const launchControlInput = inputs.find((input: any) => 
      input.name?.toLowerCase().includes('launch control')
    );
    
    if (!launchControlInput) return null;
    
    const controller: SessionMidiController = {
      id: launchControlInput.id,
      name: 'Launch Control XL',
      type: 'launchControl',
      isConnected: true,
      channelStrips: this.createLaunchControlStrips(),
      globalControls: [
        { name: 'Master Tempo', ccNumber: 14, value: 64, function: 'masterTempo' },
        { name: 'Global Volume', ccNumber: 15, value: 100, function: 'globalVolume' },
        { name: 'Scene Select', ccNumber: 16, value: 0, function: 'sceneSelect' }
      ],
      currentValues: {}
    };
    
    this.activeController = controller;
    console.log('🎮 Launch Control XL detected and configured');
    this.emitUpdate();
    return controller;
  }
  
  // Crear configuración de strips para Launch Control XL
  private createLaunchControlStrips(): ChannelStrip[] {
    const strips: ChannelStrip[] = [];
    
    for (let i = 1; i <= 8; i++) {
      strips.push({
        stripIndex: i,
        controls: {
          fader: 77 + i - 1,       // CC 77-84 (faders)
          knob1: 13 + (i - 1),     // CC 13-20 (top knobs)
          knob2: 29 + (i - 1),     // CC 29-36 (middle knobs)
          knob3: 49 + (i - 1),     // CC 49-56 (bottom knobs)
          button1: 41 + i - 1,     // CC 41-48 (upper buttons)
          button2: 57 + i - 1      // CC 57-64 (lower buttons)
        },
        values: {
          fader: 0,
          knob1: 0,
          knob2: 0,
          knob3: 0,
          button1: false,
          button2: false
        }
      });
    }
    
    return strips;
  }
  
  // Configurar listeners MIDI
  private setupMidiListeners() {
    if (!this.midiAccess) return;
    
    const inputs = Array.from(this.midiAccess.inputs.values());
    inputs.forEach((input: any) => {
      input.onmidimessage = (message: any) => {
        this.handleMidiMessage(message.data);
      };
    });
  }
  
  // Procesar mensajes MIDI entrantes
  private handleMidiMessage(data: Uint8Array) {
    const [status, cc, value] = data;
    
    // Process Control Change messages on any MIDI channel
    if ((status & 0xf0) !== 0xb0) return;
    
    if (!this.activeController) return;
    
    // Actualizar valor actual
    this.activeController.currentValues[cc] = value;
    
    // Determinar qué strip y control
    const stripIndex = this.determineStripFromCC(cc);
    const controlType = this.determineControlType(cc);
    
    if (stripIndex && controlType) {
      this.handleStripControl(stripIndex, controlType, value);
    }
    
    // Controles globales
    this.handleGlobalControl(cc, value);
  }
  
  // Determinar strip desde CC number
  private determineStripFromCC(cc: number): number | null {
    // Faders: CC 77-84
    if (cc >= 77 && cc <= 84) return cc - 76;

    // Knobs
    if (cc >= 13 && cc <= 20) return cc - 12; // top row
    if (cc >= 29 && cc <= 36) return cc - 28; // middle row
    if (cc >= 49 && cc <= 56) return cc - 48; // bottom row

    // Buttons
    if (cc >= 41 && cc <= 48) return cc - 40; // upper buttons
    if (cc >= 57 && cc <= 64) return cc - 56; // lower buttons
    
    return null;
  }
  
  // Determinar tipo de control
  private determineControlType(cc: number): string | null {
    if (cc >= 77 && cc <= 84) return 'fader';
    if (cc >= 13 && cc <= 20) return 'knob1';
    if (cc >= 29 && cc <= 36) return 'knob2';
    if (cc >= 49 && cc <= 56) return 'knob3';
    if (cc >= 41 && cc <= 48) return 'button1';
    if (cc >= 57 && cc <= 64) return 'button2';
    return null;
  }
  
  private handleStripControl(stripIndex: number, control: string, value: number) {
    if (!this.activeController) return;
    const strip = this.activeController.channelStrips[stripIndex - 1];
    if (!strip) return;
    
    switch (control) {
      case 'fader':
        strip.values.fader = value;
        break;
      case 'knob1':
        strip.values.knob1 = value;
        break;
      case 'knob2':
        strip.values.knob2 = value;
        break;
      case 'knob3':
        strip.values.knob3 = value;
        break;
      case 'button1':
        strip.values.button1 = value > 0;
        break;
      case 'button2':
        strip.values.button2 = value > 0;
        break;
    }
    this.emitUpdate();
  }

  private handleGlobalControl(cc: number, value: number) {
    if (!this.activeController) return;
    const control = this.activeController.globalControls.find(c => c.ccNumber === cc);
    if (!control) return;
    control.value = value;
    this.emitUpdate();
  }
  
  // Mapear un track a un strip específico
  mapTrackToStrip(stripIndex: number, trackId: string) {
    this.trackMapping.set(stripIndex, trackId);
    this.emitUpdate();
  }
  
  // Desmapear track de strip
  unmapTrack(stripIndex: number) {
    this.trackMapping.delete(stripIndex);
    this.emitUpdate();
  }

  // Subscribe to controller updates
  onUpdate(callback: (ctrl: SessionMidiController) => void): () => void {
    this.listeners.push(callback);
    if (this.activeController) {
      callback(this.activeController);
    }
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  private emitUpdate() {
    if (!this.activeController) return;
    this.listeners.forEach(cb => cb(this.activeController!));
  }
}

