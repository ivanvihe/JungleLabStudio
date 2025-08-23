import { MidiClip, MidiNote, TrackType, MusicalContext } from '../types/CrealabTypes';
import { MusicTheoryUtils, HARMONIC_PROGRESSIONS } from '../utils/musicTheory';
import { generateEuclideanPattern, EUCLIDEAN_PATTERNS } from '../utils/euclideanPatterns';

export class MidiClipGenerator {
  private static instance: MidiClipGenerator;
  
  static getInstance(): MidiClipGenerator {
    if (!this.instance) {
      this.instance = new MidiClipGenerator();
    }
    return this.instance;
  }

  generateKick(
    style: 'minimal' | 'dub' | 'hypnotic' | 'fourOnFloor' = 'dub',
    measures: number = 4,
    channel: number = 10
  ): MidiClip {
    const pattern = generateEuclideanPattern('kick', style);
    const notes: MidiNote[] = [];
    
    for (let measure = 0; measure < measures; measure++) {
      pattern.forEach((hit, step) => {
        if (hit) {
          notes.push({
            note: 36, // C2 kick
            time: (measure * pattern.length + step) * (4 / pattern.length), // Convert to beats
            velocity: this.generateVelocityVariation(80, 20), // Humanization
            duration: 0.25 // Quarter beat
          });
        }
      });
    }
    
    return {
      id: `kick-${Date.now()}`,
      name: `Kick ${style}`,
      trackType: 'kick',
      notes,
      duration: measures,
      channel,
      enabled: true
    };
  }

  generateBass(
    key: string = 'C',
    scale: string = 'minor',
    style: 'dub' | 'minimal' | 'hypnotic' = 'dub',
    measures: number = 4,
    channel: number = 1
  ): MidiClip {
    const scaleNotes = MusicTheoryUtils.getScaleNotes(key, scale);
    const pattern = generateEuclideanPattern('bass', style);
    const notes: MidiNote[] = [];
    
    // Focus on root and fifth for dub bass
    const bassNotes = [scaleNotes[0], scaleNotes[4]]; // Root and fifth
    
    for (let measure = 0; measure < measures; measure++) {
      pattern.forEach((hit, step) => {
        if (hit) {
          const noteChoice = bassNotes[Math.floor(Math.random() * bassNotes.length)];
          const octave = Math.random() > 0.8 ? '1' : '2'; // Mostly C2, sometimes C1
          
          notes.push({
            note: MusicTheoryUtils.noteToMidi(noteChoice + octave),
            time: (measure * pattern.length + step) * (4 / pattern.length),
            velocity: this.generateVelocityVariation(70, 25),
            duration: 0.75 // Longer bass notes
          });
        }
      });
    }
    
    return {
      id: `bass-${Date.now()}`,
      name: `Bass ${style}`,
      trackType: 'bass',
      notes,
      duration: measures,
      channel,
      enabled: true
    };
  }

  generateArpeggio(
    key: string = 'C',
    scale: string = 'dorian',
    style: 'floating' | 'ambient' | 'maxCooper' = 'floating',
    measures: number = 4,
    channel: number = 2
  ): MidiClip {
    const scaleNotes = MusicTheoryUtils.getScaleNotes(key, scale);
    const pattern = generateEuclideanPattern('hihat', style); // Using hihat patterns for arps
    const notes: MidiNote[] = [];
    
    for (let measure = 0; measure < measures; measure++) {
      pattern.forEach((hit, step) => {
        if (hit) {
          // Arpeggio pattern: cycle through scale notes
          const noteIndex = step % scaleNotes.length;
          const octave = Math.floor(step / scaleNotes.length) + 4; // Start from octave 4
          
          notes.push({
            note: MusicTheoryUtils.noteToMidi(scaleNotes[noteIndex] + octave),
            time: (measure * pattern.length + step) * (4 / pattern.length),
            velocity: this.generateVelocityVariation(50, 30), // Softer for ambient
            duration: 0.5
          });
        }
      });
    }
    
    return {
      id: `arp-${Date.now()}`,
      name: `Arp ${style}`,
      trackType: 'arp',
      notes,
      duration: measures,
      channel,
      enabled: true
    };
  }

  generateChordProgression(
    key: string = 'C',
    progression: keyof typeof HARMONIC_PROGRESSIONS = 'dubClassic',
    measures: number = 4,
    channel: number = 3
  ): MidiClip {
    const chordRomans = HARMONIC_PROGRESSIONS[progression];
    const notes: MidiNote[] = [];
    const beatsPerChord = (measures * 4) / chordRomans.length;
    
    chordRomans.forEach((roman, index) => {
      const chordNotes = MusicTheoryUtils.getChordFromRomanNumeral(roman, key);
      const startTime = index * beatsPerChord;
      
      chordNotes.forEach(note => {
        notes.push({
          note: MusicTheoryUtils.noteToMidi(note + '3'), // Chord in octave 3
          time: startTime,
          velocity: this.generateVelocityVariation(60, 20),
          duration: beatsPerChord * 0.9 // Slightly shorter than full duration
        });
      });
    });
    
    return {
      id: `chords-${Date.now()}`,
      name: `${progression} in ${key}`,
      trackType: 'fx', // Using fx as chord track
      notes,
      duration: measures,
      channel,
      enabled: true
    };
  }

  private generateVelocityVariation(base: number, variation: number): number {
    const min = Math.max(1, base - variation);
    const max = Math.min(127, base + variation);
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }
}

