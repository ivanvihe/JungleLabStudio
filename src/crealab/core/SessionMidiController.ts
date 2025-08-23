import { SessionMidiController, ChannelStrip } from '../types/GeneratorTypes';
import { GeneratorEngine } from './GeneratorEngine';

export class SessionMidiManager {
  private static instance: SessionMidiManager;
  private midiAccess: any = null;
  private activeController: SessionMidiController | null = null;
  private trackMapping: Map<number, string> = new Map(); // strip -> trackId
  
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
    return controller;
  }
  
  // Crear configuración de strips para Launch Control XL
  private createLaunchControlStrips(): ChannelStrip[] {
    const strips: ChannelStrip[] = [];
    
    for (let i = 1; i <= 8; i++) {
      strips.push({
        stripIndex: i,
        controls: {
          fader: 77 + i - 1,      // CC 77-84 (faders)
          knob1: 13 + (i - 1) * 4,  // CC 13, 17, 21, 25, 29, 33, 37, 41 (knobs superiores)
          knob2: 14 + (i - 1) * 4,  // CC 14, 18, 22, 26, 30, 34, 38, 42 (knobs medios)
          knob3: 15 + (i - 1) * 4,  // CC 15, 19, 23, 27, 31, 35, 39, 43 (knobs inferiores)
          button1: 41 + i - 1,       // CC 41-48 (botones superiores)
          button2: 57 + i - 1        // CC 57-64 (botones inferiores)
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
    
    // Solo procesar Control Change (176 = 0xB0 + channel 0)
    if (status !== 176) return;
    
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
    
    // Knobs: CC 13-15, 17-19, 21-23, 25-27, 29-31, 33-35, 37-39, 41-43
    if (cc >= 13 && cc <= 43) {
      return Math.floor((cc - 13) / 4) + 1;
    }
    
    // Buttons: CC 41-48, 57-64
    if (cc >= 41 && cc <= 48) return cc - 40;
    if (cc >= 57 && cc <= 64) return cc - 56;
    
    return null;
  }
  
  // Determinar tipo de control
  private determineControlType(cc: number): string | null {
    if (cc >= 77 && cc <= 84) return 'fader';
    if ([13,17,21,25,29,33,37,41].includes(cc)) return 'knob1';
    if ([14,18,22,26,30,34,38,42].includes(cc)) return 'knob2';
    if ([15,19,23,27,31,35,39,43].includes(cc)) return 'knob3';
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
        this.updateGenerator(strip, 'density', value / 127);
        break;
      case 'knob2':
        strip.values.knob2 = value;
        this.updateGenerator(strip, 'probability', value / 127);
        break;
      case 'knob3':
        strip.values.knob3 = value;
        this.updateGenerator(strip, 'velocity', value / 127);
        break;
      case 'button1':
        strip.values.button1 = value > 0;
        break;
      case 'button2':
        strip.values.button2 = value > 0;
        break;
    }
  }
  
  private handleGlobalControl(cc: number, value: number) {
    if (!this.activeController) return;
    const control = this.activeController.globalControls.find(c => c.ccNumber === cc);
    if (!control) return;
    control.value = value;
  }
  
  private updateGenerator(strip: ChannelStrip, control: string, value: number) {
    const trackId = this.trackMapping.get(strip.stripIndex);
    if (!trackId) return;
    GeneratorEngine.getInstance().updateGeneratorControl(trackId, control, value);
  }
  
  // Mapear un track a un strip específico
  mapTrackToStrip(stripIndex: number, trackId: string) {
    this.trackMapping.set(stripIndex, trackId);
  }
  
  // Desmapear track de strip
  unmapTrack(stripIndex: number) {
    this.trackMapping.delete(stripIndex);
  }
}

