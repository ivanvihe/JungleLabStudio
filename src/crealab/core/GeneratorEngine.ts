import { GenerativeTrack, GeneratorType, MidiNote } from '../types/CrealabTypes';
import { EuclideanGenerator } from '../generators/EuclideanGenerator';
import { ProbabilisticGenerator } from '../generators/ProbabilisticGenerator';
import { MarkovGenerator } from '../generators/MarkovGenerator';
import { ArpeggiatorGenerator } from '../generators/ArpeggiatorGenerator';
import { ChaosGenerator } from '../generators/ChaosGenerator';

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

  static getInstance(): GeneratorEngine {
    if (!this.instance) {
      this.instance = new GeneratorEngine();
    }
    return this.instance;
  }

  constructor() {
    this.initializeGenerators();
  }

  private initializeGenerators() {
    // Crear instancias de todos los generadores
    this.generators.set('euclidean', new EuclideanGenerator());
    this.generators.set('probabilistic', new ProbabilisticGenerator());
    this.generators.set('markov', new MarkovGenerator());
    this.generators.set('arpeggiator', new ArpeggiatorGenerator());
    this.generators.set('chaos', new ChaosGenerator());
  }

  // Iniciar el motor generativo
  start(tracks: GenerativeTrack[], globalTempo: number, key: string, scale: string) {
    if (this.isRunning) return;

    this.isRunning = true;
    this.currentTime = 0;

    // Calcular intervalo basado en el tempo (16th notes)
    const interval = (60 / globalTempo / 4) * 1000; // milliseconds

    this.intervalId = setInterval(() => {
      this.tick(tracks, globalTempo, key, scale);
    }, interval);

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
    console.log('🛑 Generator Engine stopped');
  }

  // Tick principal - ejecuta cada 16th note
  private tick(tracks: GenerativeTrack[], globalTempo: number, key: string, scale: string) {
    tracks.forEach(track => {
      if (track.generator.enabled && track.controls.playStop) {
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

    // Generar notas
    const notes = generator.generate(track, this.currentTime, globalTempo, key, scale);

    // Enviar notas MIDI si hay alguna
    if (notes.length > 0) {
      this.sendMidiNotes(notes, track);
    }
  }

  // Enviar notas MIDI al dispositivo externo
  private async sendMidiNotes(notes: MidiNote[], track: GenerativeTrack) {
    if (!track.outputDevice) return;

    try {
      const access = await (navigator as any).requestMIDIAccess();
      const output = access.outputs.get(track.outputDevice);
      
      if (!output) return;

      notes.forEach(note => {
        // Note On
        const noteOnMsg = [
          0x90 + (track.midiChannel - 1), // Note on + channel
          note.note,
          note.velocity
        ];
        output.send(noteOnMsg);

        // Note Off (programado)
        setTimeout(() => {
          const noteOffMsg = [
            0x80 + (track.midiChannel - 1), // Note off + channel
            note.note,
            0
          ];
          output.send(noteOffMsg);
        }, note.duration * 1000); // Convert to milliseconds
      });

    } catch (error) {
      console.warn('Failed to send MIDI notes:', error);
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
