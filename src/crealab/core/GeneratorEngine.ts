import { GenerativeTrack, GeneratorType, MidiNote } from '../types/CrealabTypes';
import { EuclideanGenerator } from '../generators/EuclideanGenerator';
import { ProbabilisticGenerator } from '../generators/ProbabilisticGenerator';
import { MarkovGenerator } from '../generators/MarkovGenerator';
import { ArpeggiatorGenerator } from '../generators/ArpeggiatorGenerator';
import { ChaosGenerator } from '../generators/ChaosGenerator';
import { MagentaGenerator } from '../generators/MagentaGenerator';
import { LSystemGenerator } from '../generators/advanced/LSystemGenerator';
import { CellularAutomataGenerator } from '../generators/advanced/CellularAutomataGenerator';
import { NeuralNetworkGenerator } from '../generators/advanced/NeuralNetworkGenerator';
import { BasslineGenerator } from '../generators/BasslineGenerator';
import { MusicalIntelligence } from '../ai/MusicalIntelligence';
import { MidiManager } from './MidiManager';

export interface GeneratorInstance {
  generate(
    track: GenerativeTrack,
    currentTime: number,
    globalTempo: number,
    key: string,
    scale: string
  ): MidiNote[];
  
  updateParameters(track: GenerativeTrack): void;
  reset(): void;
}

export class GeneratorEngine {
  private static instance: GeneratorEngine;
  private generators: Map<string, GeneratorInstance> = new Map();
  private isRunning: boolean = false;
  private currentTime: number = 0;
  private intervalId: NodeJS.Timeout | null = null;
  private tracks: GenerativeTrack[] = [];
  private broadcast: BroadcastChannel | null = null;

  static getInstance(): GeneratorEngine {
    if (!this.instance) {
      this.instance = new GeneratorEngine();
    }
    return this.instance;
  }

  constructor() {
    this.initializeGenerators();
    try {
      this.broadcast = new BroadcastChannel('av-sync');
    } catch (e) {
      console.warn('BroadcastChannel not available', e);
    }
  }

  private initializeGenerators() {
    // Crear instancias de todos los generadores
    this.generators.set('euclidean', new EuclideanGenerator());
    this.generators.set('probabilistic', new ProbabilisticGenerator());
    this.generators.set('markov', new MarkovGenerator());
    this.generators.set('arpeggiator', new ArpeggiatorGenerator());
    this.generators.set('chaos', new ChaosGenerator());
      this.generators.set('magenta', new MagentaGenerator());
      this.generators.set('lsystem', new LSystemGenerator());
      this.generators.set('cellular', new CellularAutomataGenerator());
      this.generators.set('neural', new NeuralNetworkGenerator());
      this.generators.set('bassline', new BasslineGenerator());
    }

  // Iniciar el motor generativo
  start(tracks: GenerativeTrack[], globalTempo: number, key: string, scale: string) {
    if (this.isRunning) return;

    this.tracks = tracks;
    this.isRunning = true;
    this.currentTime = 0;

    // Calcular intervalo basado en el tempo (16th notes)
    const interval = (60 / globalTempo / 4) * 1000; // milliseconds

    this.intervalId = setInterval(() => {
      this.tick(globalTempo, key, scale);
    }, interval);

    // Enviar mensajes de inicio de clock si están habilitados
    this.tracks.forEach(t => {
      if (t.sendClock) {
        this.sendMidiStart(t);
        if (!this.tracksWithClock.includes(t)) {
          this.tracksWithClock.push(t);
        }
      }
    });

    console.log('🎵 Generator Engine started at', globalTempo, 'BPM');
  }

  // Detener el motor
  stop() {
    if (!this.isRunning) return;

    this.isRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    // Reset all generators
    this.generators.forEach(generator => generator.reset());

     // Enviar mensajes de stop a dispositivos que usan clock
    this.tracksWithClock.forEach(t => this.sendMidiStop(t));
    this.tracksWithClock = [];
    console.log('🛑 Generator Engine stopped');
  }

  // Tick principal - ejecuta cada 16th note
  private tracksWithClock: GenerativeTrack[] = [];

  updateTracks(tracks: GenerativeTrack[]) {
    this.tracks = tracks;
  }

  private tick(globalTempo: number, key: string, scale: string) {
    MusicalIntelligence.applyCrossTrackInfluence(this.tracks);
    MusicalIntelligence.analyzeHarmony(this.tracks);

    this.tracks.forEach(track => {
      if (track.sendClock && !this.tracksWithClock.includes(track)) {
        this.tracksWithClock.push(track);
      }

      if (track.sendClock) {
        this.sendMidiClock(track, 6);
      }

      if (track.generator.enabled) {
        this.processTrack(track, globalTempo, key, scale);
      }
    });

    this.currentTime += 0.25; // Incrementar por 16th note
  }

  // Procesar un track individual
  private processTrack(
    track: GenerativeTrack, 
    globalTempo: number, 
    key: string, 
    scale: string
  ) {
    const generator = this.generators.get(track.generator.type);
    if (!generator) return;

    // Actualizar parámetros del generador basado en controles
    generator.updateParameters(track);
    MusicalIntelligence.evolvePattern(track);

    // Generar notas
    const notes = generator.generate(track, this.currentTime, globalTempo, key, scale);

    // Enviar notas MIDI si hay alguna
    if (notes.length > 0) {
      // Notificar que el generador produjo notas
      track.generator.lastNoteTime = this.currentTime;
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('generatorNote', { detail: { trackId: track.id } })
        );
      }

      this.sendMidiNotes(notes, track, globalTempo);
    }
  }

  // Enviar notas MIDI al dispositivo externo
  private async sendMidiNotes(
    notes: MidiNote[],
    track: GenerativeTrack,
    globalTempo: number
  ) {
    if (!track.outputDevice) {
      console.warn(`No output device configured for track ${track.name}`);
      return;
    }

    const midi = MidiManager.getInstance();
    const beatDuration = (60 / globalTempo) * 1000; // ms per beat

    await Promise.all(
      notes.map(n =>
        midi.sendNote(
          track.outputDevice!,
          track.midiChannel,
          n.note,
          n.velocity,
          n.duration * beatDuration
        )
      )
    );

    // Notificar que se enviaron notas al dispositivo
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('trackNote', { detail: { trackId: track.id } })
      );
    }

    if (this.broadcast && track.visualLayer && typeof track.visualPad === 'number') {
      notes.forEach(note => {
        this.broadcast!.postMessage({
          type: 'midiTrigger',
          data: {
            layerId: track.visualLayer,
            note: track.visualPad,
            velocity: note.velocity
          }
        });
      });
    }
  }

  // Enviar mensajes de clock
  private async sendMidiClock(track: GenerativeTrack, pulses: number) {
    if (!track.outputDevice) return;
    try {
      const access = await (navigator as any).requestMIDIAccess();
      const output = access.outputs.get(track.outputDevice);
      if (!output) return;
      for (let i = 0; i < pulses; i++) {
        output.send([0xf8]);
      }
    } catch (err) {
      console.warn('Failed to send MIDI clock:', err);
    }
  }

  private async sendMidiStart(track: GenerativeTrack) {
    await this.sendMidiMessage(track, 0xfa);
  }

  private async sendMidiStop(track: GenerativeTrack) {
    await this.sendMidiMessage(track, 0xfc);
  }

  private async sendMidiMessage(track: GenerativeTrack, msg: number) {
    if (!track.outputDevice) return;
    try {
      const access = await (navigator as any).requestMIDIAccess();
      const output = access.outputs.get(track.outputDevice);
      if (!output) return;
      output.send([msg]);
    } catch (err) {
      console.warn('Failed to send MIDI message:', err);
    }
  }

  // Actualizar parámetros de un track específico
  updateTrackParameters(track: GenerativeTrack) {
    const generator = this.generators.get(track.generator.type);
    if (generator) {
      generator.updateParameters(track);
    }
  }

  // Cambiar tipo de generador
  changeGeneratorType(track: GenerativeTrack, newType: GeneratorType) {
    // Reset del generador anterior
    const oldGenerator = this.generators.get(track.generator.type);
    if (oldGenerator) {
      oldGenerator.reset();
    }

    // Configurar nuevo generador
    track.generator.type = newType;
    track.generator.enabled = newType !== 'off';

    // Configurar parámetros por defecto según el tipo
    this.setDefaultParameters(track, newType);
  }

  // Configurar parámetros por defecto según el tipo de generador
  private setDefaultParameters(track: GenerativeTrack, type: GeneratorType) {
    switch (type) {
      case 'euclidean':
        track.generator.parameters = { pulses: 8, steps: 16, offset: 0, mutation: 0.1 };
        break;
      case 'probabilistic':
        track.generator.parameters = { density: 0.5, variation: 0.3, swing: 0.1 };
        break;
      case 'markov':
        track.generator.parameters = { order: 2, creativity: 0.5, memory: 8 };
        break;
      case 'arpeggiator':
        track.generator.parameters = { pattern: 'up', octaves: 2, noteLength: 0.25 };
        break;
      case 'chaos':
        track.generator.parameters = { attractor: 'lorenz', sensitivity: 0.5, scaling: 1.0 };
        break;
      case 'magenta':
        track.generator.parameters = { steps: 32, temperature: 1.0 };
        break;
      case 'lsystem':
        track.generator.parameters = { rules: { A: 'AB', B: 'A' } };
        break;
      case 'cellular':
        track.generator.parameters = { seed: [1] };
        break;
      case 'neural':
        track.generator.parameters = {};
        break;
      case 'bassline':
        track.generator.parameters = { pattern: 'dub', variation: 0 };
        break;
      default:
        track.generator.parameters = {};
    }
  }

  // Getters
  getCurrentTime(): number {
    return this.currentTime;
  }

  isGeneratorRunning(): boolean {
    return this.isRunning;
  }

  getAvailableGenerators(): GeneratorType[] {
    return Array.from(this.generators.keys()) as GeneratorType[];
  }
}
