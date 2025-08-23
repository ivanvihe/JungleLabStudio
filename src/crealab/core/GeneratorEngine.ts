import { MidiGenerator, GeneratorType, EuclideanParams, MarkovParams, ProbabilisticParams } from '../types/GeneratorTypes';
import { MidiNote } from '../types/CrealabTypes';
import { euclideanRhythm } from '../utils/euclideanPatterns';

export class GeneratorEngine {
  private static instance: GeneratorEngine;
  private activeGenerators: Map<string, MidiGenerator> = new Map();
  private schedulerInterval: NodeJS.Timeout | null = null;
  private isRunning = false;
  
  // MIDI Access para output
  private midiAccess: any = null;
  
  static getInstance(): GeneratorEngine {
    if (!this.instance) {
      this.instance = new GeneratorEngine();
    }
    return this.instance;
  }
  
  async initialize() {
    try {
      this.midiAccess = await (navigator as any).requestMIDIAccess();
      console.log('🎛️ Generator Engine initialized');
    } catch (error) {
      console.error('❌ Failed to initialize MIDI:', error);
    }
  }
  
  // Iniciar el motor de generación
  start() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.schedulerInterval = setInterval(() => {
      this.processGenerators();
    }, 16); // 60 FPS para precisión
    
    console.log('▶️ Generator Engine started');
  }
  
  stop() {
    this.isRunning = false;
    if (this.schedulerInterval) {
      clearInterval(this.schedulerInterval);
      this.schedulerInterval = null;
    }
    console.log('⏹️ Generator Engine stopped');
  }
  
  // Procesar todos los generadores activos
  private processGenerators() {
    const currentTime = performance.now() / 1000; // Tiempo en segundos
    
    this.activeGenerators.forEach((generator, id) => {
      if (generator.isActive && generator.isPlaying) {
        const note = this.generateNote(generator, currentTime);
        if (note) {
          this.sendMidiNote(generator, note);
          generator.generatedNotes.push(note);
          generator.lastNoteTime = currentTime;
        }
      }
    });
  }
  
  // Registrar un generador
  registerGenerator(generator: MidiGenerator): void {
    this.activeGenerators.set(generator.id, generator);
    console.log(`🔄 Generator registered: ${generator.name}`);
  }
  
  // Desregistrar un generador
  unregisterGenerator(generatorId: string): void {
    this.activeGenerators.delete(generatorId);
    console.log(`❌ Generator unregistered: ${generatorId}`);
  }
  
  // Generar nota según el tipo de generador
  private generateNote(generator: MidiGenerator, currentTime: number): MidiNote | null {
    switch (generator.type) {
      case 'euclidean':
        return this.generateEuclideanNote(generator, currentTime);
      case 'markov':
        return this.generateMarkovNote(generator, currentTime);
      case 'probabilistic':
        return this.generateProbabilisticNote(generator, currentTime);
      case 'arpeggiator':
        return this.generateArpeggiatorNote(generator, currentTime);
      default:
        return null;
    }
  }
  
  // Generador Euclidiano
  private generateEuclideanNote(generator: MidiGenerator, currentTime: number): MidiNote | null {
    const params = generator.parameters.euclidean!;
    const controls = generator.realTimeControls;
    
    // Generar patrón euclidiano
    const pattern = euclideanRhythm(
      Math.floor(params.pulses * controls.density),
      params.steps,
      params.offset
    );
    
    // Verificar si debe tocar en este step
    const stepDuration = (60 / generator.parameters.tempo) / 4; // Duración de 16th note
    const timeSinceLastNote = currentTime - generator.lastNoteTime;
    
    if (timeSinceLastNote < stepDuration) return null;
    
    const currentStepInPattern = generator.currentStep % params.steps;
    const shouldTrigger = pattern[currentStepInPattern] && 
                         Math.random() < controls.probability;
    
    generator.currentStep++;
    
    if (!shouldTrigger) return null;
    
    // Seleccionar nota del pool
    const notePool = generator.parameters.notePool;
    const baseNote = notePool[Math.floor(Math.random() * notePool.length)];
    const octaveShift = Math.floor((controls.octave - 0.5) * 6) * 12; // -3 to +3 octaves
    
    return {
      note: baseNote + octaveShift,
      time: currentTime,
      velocity: Math.floor(80 * controls.velocity + Math.random() * 20 * controls.chaos),
      duration: stepDuration * (1 + controls.swing * 0.5)
    };
  }
  
  // Generador de Cadenas de Markov
  private generateMarkovNote(generator: MidiGenerator, currentTime: number): MidiNote | null {
    const params = generator.parameters.markov!;
    const controls = generator.realTimeControls;
    
    // Implementación simplificada de Markov
    const recentNotes = generator.generatedNotes
      .slice(-params.order)
      .map(n => n.note);
    
    if (recentNotes.length < params.order) {
      // Empezar con nota aleatoria del pool
      const notePool = generator.parameters.notePool;
      const note = notePool[Math.floor(Math.random() * notePool.length)];
      
      return {
        note,
        time: currentTime,
        velocity: Math.floor(70 * controls.velocity),
        duration: 0.25
      };
    }
    
    // Generar siguiente nota basada en contexto
    // (Implementación simplificada - en producción usar cadena entrenada)
    const notePool = generator.parameters.notePool;
    const creativity = params.creativity * controls.chaos;
    
    let nextNote;
    if (Math.random() < creativity) {
      // Nota creativa/aleatoria
      nextNote = notePool[Math.floor(Math.random() * notePool.length)];
    } else {
      // Nota basada en patrón (simplificado)
      const lastNote = recentNotes[recentNotes.length - 1];
      const direction = Math.random() > 0.5 ? 1 : -1;
      const interval = Math.floor(Math.random() * 4) + 1; // 1-4 semitones
      nextNote = lastNote + (direction * interval);
      
      // Mantener dentro del rango
      nextNote = Math.max(Math.min(nextNote, Math.max(...notePool)), Math.min(...notePool));
    }
    
    return {
      note: nextNote,
      time: currentTime,
      velocity: Math.floor(60 * controls.velocity + Math.random() * 40),
      duration: 0.25 + Math.random() * 0.5
    };
  }
  
  // Generador Probabilístico
  private generateProbabilisticNote(generator: MidiGenerator, currentTime: number): MidiNote | null {
    const params = generator.parameters.probabilistic!;
    const controls = generator.realTimeControls;
    
    // Verificar timing basado en patrón rítmico
    const beatDuration = 60 / generator.parameters.tempo;
    const timeSinceLastNote = currentTime - generator.lastNoteTime;
    
    if (timeSinceLastNote < beatDuration / 4) return null; // 16th note grid
    
    // Probabilidad de trigger basada en controles
    if (Math.random() > controls.probability * controls.density) return null;
    
    // Seleccionar nota basada en pesos
    const weightedNotes = Object.entries(params.noteWeights);
    const totalWeight = weightedNotes.reduce((sum, [_, weight]) => sum + weight, 0);
    const random = Math.random() * totalWeight;
    
    let accumulator = 0;
    for (const [noteStr, weight] of weightedNotes) {
      accumulator += weight;
      if (random <= accumulator) {
        return {
          note: parseInt(noteStr),
          time: currentTime,
          velocity: Math.floor(50 + controls.velocity * 60 + controls.chaos * 20),
          duration: 0.25 + Math.random() * controls.swing
        };
      }
    }
    
    return null;
  }
  
  // Arpegiador generativo
  private generateArpeggiatorNote(generator: MidiGenerator, currentTime: number): MidiNote | null {
    const params = generator.parameters.arpeggiator!;
    const controls = generator.realTimeControls;
    
    const beatDuration = 60 / generator.parameters.tempo;
    const noteDuration = beatDuration / 4; // 16th notes
    const timeSinceLastNote = currentTime - generator.lastNoteTime;
    
    if (timeSinceLastNote < noteDuration) return null;
    
    // Probabilidad de trigger
    if (Math.random() > controls.probability) return null;
    
    // Generar arpeggio
    const notePool = generator.parameters.notePool.sort((a, b) => a - b);
    const arpIndex = generator.currentStep % notePool.length;
    
    let note;
    switch (params.pattern) {
      case 'up':
        note = notePool[arpIndex];
        break;
      case 'down':
        note = notePool[notePool.length - 1 - arpIndex];
        break;
      case 'upDown':
        const cycle = (notePool.length - 1) * 2;
        const pos = generator.currentStep % cycle;
        note = pos < notePool.length 
          ? notePool[pos] 
          : notePool[cycle - pos];
        break;
      case 'random':
        note = notePool[Math.floor(Math.random() * notePool.length)];
        break;
      default:
        note = notePool[arpIndex];
    }
    
    generator.currentStep++;
    
    return {
      note: note + Math.floor((controls.octave - 0.5) * 6) * 12,
      time: currentTime,
      velocity: Math.floor(60 + controls.velocity * 50),
      duration: params.noteLength * (1 + controls.swing)
    };
  }
  
  // Enviar nota MIDI
  private sendMidiNote(generator: MidiGenerator, note: MidiNote) {
    if (!this.midiAccess) return;
    
    // Buscar el output device apropiado
    // (Esto se conectaría con la configuración del track)
    const outputs = Array.from(this.midiAccess.outputs.values());
    if (outputs.length === 0) return;
    
    const output = outputs[0]; // Por ahora usar el primer dispositivo
    
    // Note On
    output.send([
      0x90, // Note on, channel 1
      note.note,
      note.velocity
    ]);
    
    // Note Off programado
    setTimeout(() => {
      output.send([
        0x80, // Note off, channel 1
        note.note,
        0
      ]);
    }, note.duration * 1000);
  }
  
  // Control en tiempo real
  updateGeneratorControl(generatorId: string, control: string, value: number) {
    const generator = this.activeGenerators.get(generatorId);
    if (!generator) return;
    
    if (control in generator.realTimeControls) {
      (generator.realTimeControls as any)[control] = value;
    }
  }
}

