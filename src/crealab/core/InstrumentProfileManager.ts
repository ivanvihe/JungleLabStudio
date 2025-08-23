import { InstrumentProfile, GenerativeTrack, GeneratorType } from '../types/CrealabTypes';
import { INSTRUMENT_PROFILES, getProfileById, getProfilesByGenre } from '../data/InstrumentProfiles';

export class InstrumentProfileManager {
  private static instance: InstrumentProfileManager;

  static getInstance(): InstrumentProfileManager {
    if (!this.instance) {
      this.instance = new InstrumentProfileManager();
    }
    return this.instance;
  }

  // Aplicar perfil de instrumento a un track
  applyProfileToTrack(track: GenerativeTrack, profileId: string): Partial<GenerativeTrack> {
    const profile = getProfileById(profileId);
    if (!profile) return {};

    console.log(`🎺 Applying profile "${profile.name}" to track ${track.trackNumber}`);

    const updates: Partial<GenerativeTrack> = {
      instrumentProfile: profileId,
      color: profile.color,
      
      // Actualizar generador sugerido si el actual es 'off'
      generator: track.generator.type === 'off' ? {
        ...track.generator,
        type: profile.suggestedGenerators[0] as GeneratorType,
        enabled: true,
        parameters: this.getDefaultParametersForGenerator(
          profile.suggestedGenerators[0] as GeneratorType,
          profile
        )
      } : track.generator
    };

    return updates;
  }

  // Obtener parámetros por defecto para un generador basado en el perfil
  private getDefaultParametersForGenerator(
    generatorType: GeneratorType, 
    profile: InstrumentProfile
  ): Record<string, any> {
    const baseParams = profile.defaultParameters;
    
    switch (generatorType) {
      case 'euclidean':
        return {
          pulses: baseParams.pulses || 8,
          steps: baseParams.steps || 16,
          offset: 0,
          mutation: baseParams.mutation || 0.1
        };
        
      case 'probabilistic':
        return {
          density: baseParams.density || 0.5,
          variation: 0.3,
          swing: 0.1
        };
        
      case 'markov':
        return {
          order: 2,
          creativity: baseParams.creativity || 0.5,
          memory: 8
        };
        
        case 'arpeggiator':
          return {
            pattern: baseParams.pattern || 'up',
            octaves: baseParams.octaves || 2,
            noteLength: 0.25,
            swing: 0.1
          };

        case 'bassline':
          return {
            pattern: baseParams.pattern || 'dub',
            variation: baseParams.variation || 0
          };
        
      case 'chaos':
        return {
          attractor: baseParams.attractor || 'lorenz',
          sensitivity: baseParams.sensitivity || 0.5,
          scaling: 1.0
        };
        
      default:
        return {};
    }
  }

  // Obtener sugerencias de generadores para un perfil
  getSuggestedGenerators(profileId: string): GeneratorType[] {
    const profile = getProfileById(profileId);
    return profile?.suggestedGenerators as GeneratorType[] || [];
  }

  // Obtener todos los perfiles disponibles
  getAllProfiles(): InstrumentProfile[] {
    return INSTRUMENT_PROFILES;
  }

  // Obtener perfiles por tipo
  getProfilesByType(type: string): InstrumentProfile[] {
    return INSTRUMENT_PROFILES.filter(profile => profile.type === type);
  }

  // Generar sugerencias basadas en el contexto
  generateSuggestions(
    currentTrack: GenerativeTrack,
    genre?: string,
    existingTracks?: GenerativeTrack[]
  ): InstrumentProfile[] {
    let suggestions: InstrumentProfile[] = [];

    // 1. Sugerencias basadas en género
    if (genre) {
      suggestions = getProfilesByGenre(genre);
    }

    // 2. Si no hay suficientes sugerencias, agregar por tipo
    if (suggestions.length < 3) {
      const typeProfiles = this.getProfilesByType(currentTrack.instrumentProfile ? 
        getProfileById(currentTrack.instrumentProfile)?.type || 'bass' : 'bass');
      suggestions = [...suggestions, ...typeProfiles.slice(0, 3 - suggestions.length)];
    }

    // 3. Evitar duplicados con tracks existentes
    if (existingTracks) {
      const usedProfiles = existingTracks
        .map(t => t.instrumentProfile)
        .filter(Boolean);
      
      suggestions = suggestions.filter(profile => 
        !usedProfiles.includes(profile.id));
    }

    // 4. Limitar a 5 sugerencias máximo
    return suggestions.slice(0, 5);
  }

  // Obtener información de un perfil
  getProfileInfo(profileId: string): InstrumentProfile | null {
    return getProfileById(profileId) || null;
  }

  // Crear perfil personalizado
  createCustomProfile(
    name: string,
    type: string,
    suggestedGenerators: GeneratorType[],
    defaultParameters: Record<string, any>
  ): InstrumentProfile {
    const customProfile: InstrumentProfile = {
      id: `custom_${Date.now()}`,
      name,
      brand: 'Custom',
      type: type as any,
      suggestedGenerators,
      defaultParameters,
      description: `Custom profile for ${name}`,
      color: `hsl(${Math.random() * 360}, 70%, 60%)`,
      tags: ['custom']
    };

    // En una implementación real, esto se guardaría en localStorage o BD
    console.log('📝 Custom profile created:', customProfile);
    
    return customProfile;
  }
}

