import { CreaLabProject, GenerativeTrack } from '../types/CrealabTypes';

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export class JsonValidator {
  // Validar proyecto completo
  static validateProject(project: any): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validaciones básicas
    if (!project.id) errors.push('Project ID is required');
    if (!project.name) errors.push('Project name is required');
    if (!project.tracks || !Array.isArray(project.tracks)) {
      errors.push('Project must have tracks array');
    } else if (project.tracks.length !== 8) {
      errors.push('Project must have exactly 8 tracks');
    }

    // Validar tempo
    if (typeof project.globalTempo !== 'number' || project.globalTempo < 60 || project.globalTempo > 200) {
      warnings.push('Global tempo should be between 60-200 BPM');
    }

    // Validar tracks
    if (project.tracks && Array.isArray(project.tracks)) {
      project.tracks.forEach((track: any, index: number) => {
        const trackErrors = this.validateTrack(track, index + 1);
        errors.push(...trackErrors.errors);
        warnings.push(...trackErrors.warnings);
      });
    }

    // Validar configuración de transporte
    if (project.transport) {
      const transportErrors = this.validateTransport(project.transport);
      errors.push(...transportErrors.errors);
      warnings.push(...transportErrors.warnings);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  // Validar track individual
  private static validateTrack(track: any, trackNumber: number): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const prefix = `Track ${trackNumber}:`;

    // Campos requeridos
    if (!track.id) errors.push(`${prefix} ID is required`);
    if (!track.name) errors.push(`${prefix} Name is required`);
    if (typeof track.trackNumber !== 'number' || track.trackNumber !== trackNumber) {
      errors.push(`${prefix} Track number should be ${trackNumber}`);
    }

    if (!track.trackType) {
      errors.push(`${prefix} Track type is required`);
    }

    // Validar canal MIDI
    if (typeof track.midiChannel !== 'number' || track.midiChannel < 1 || track.midiChannel > 16) {
      errors.push(`${prefix} MIDI channel must be between 1-16`);
    }

    // Validar generador
    if (!track.generator) {
      errors.push(`${prefix} Generator configuration is required`);
    } else {
      const genErrors = this.validateGenerator(track.generator, trackNumber);
      errors.push(...genErrors.errors);
      warnings.push(...genErrors.warnings);
    }

    // Validar controles
    if (!track.controls) {
      errors.push(`${prefix} Controls configuration is required`);
    } else {
      const controlErrors = this.validateControls(track.controls, trackNumber);
      errors.push(...controlErrors.errors);
      warnings.push(...controlErrors.warnings);
    }

    // Validar mapeo de Launch Control
    if (!track.launchControlMapping) {
      warnings.push(`${prefix} Launch Control mapping is missing`);
    }

    return { valid: errors.length === 0, errors, warnings };
  }

  // Validar generador
  private static validateGenerator(generator: any, trackNumber: number): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const prefix = `Track ${trackNumber} Generator:`;

    const validTypes = ['off', 'euclidean', 'probabilistic', 'markov', 'arpeggiator', 'chaos'];
    if (!validTypes.includes(generator.type)) {
      errors.push(`${prefix} Invalid generator type '${generator.type}'`);
    }

    if (typeof generator.enabled !== 'boolean') {
      warnings.push(`${prefix} 'enabled' should be boolean`);
    }

    if (!generator.parameters || typeof generator.parameters !== 'object') {
      warnings.push(`${prefix} Parameters should be an object`);
    }

    return { valid: errors.length === 0, errors, warnings };
  }

  // Validar controles
  private static validateControls(controls: any, trackNumber: number): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const prefix = `Track ${trackNumber} Controls:`;

    const requiredControls = ['intensity', 'paramA', 'paramB', 'paramC', 'playStop', 'mode'];

    requiredControls.forEach(control => {
      if (!(control in controls)) {
        errors.push(`${prefix} Missing control '${control}'`);
      }
    });

    // Validar rangos
    ['intensity', 'paramA', 'paramB', 'paramC'].forEach(control => {
      const value = controls[control];
      if (typeof value === 'number' && (value < 0 || value > 127)) {
        warnings.push(`${prefix} ${control} should be between 0-127`);
      }
    });

    return { valid: errors.length === 0, errors, warnings };
  }

  // Validar configuración de transporte
  private static validateTransport(transport: any): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    const requiredFields = ['isPlaying', 'isPaused', 'currentBeat', 'currentBar', 'currentStep'];

    requiredFields.forEach(field => {
      if (!(field in transport)) {
        warnings.push(`Transport: Missing field '${field}'`);
      }
    });

    return { valid: errors.length === 0, errors, warnings };
  }

  // Validar archivo antes de importar
  static validateImportFile(fileContent: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      const data = JSON.parse(fileContent);

      // Verificar que es un archivo de Crea Lab
      if (!data.project && !data.id) {
        errors.push('File does not appear to be a valid Crea Lab project');
        return { valid: false, errors, warnings };
      }

      // Validar estructura del proyecto
      const projectData = data.project || data;
      return this.validateProject(projectData);

    } catch (error: any) {
      errors.push(`Invalid JSON format: ${error.message}`);
      return { valid: false, errors, warnings };
    }
  }

  // Sanitizar datos de entrada
  static sanitizeProject(project: any): any {
    const sanitized = JSON.parse(JSON.stringify(project));

    // Limpiar campos potencialmente problemáticos
    if (sanitized.tracks) {
      sanitized.tracks.forEach((track: any) => {
        // Asegurar que los controles están en rango válido
        if (track.controls) {
          ['intensity', 'paramA', 'paramB', 'paramC'].forEach(control => {
            if (typeof track.controls[control] === 'number') {
              track.controls[control] = Math.max(0, Math.min(127, track.controls[control]));
            }
          });
        }

        // Validar canal MIDI
        if (track.midiChannel) {
          track.midiChannel = Math.max(1, Math.min(16, track.midiChannel));
        }
      });
    }

    // Validar tempo global
    if (sanitized.globalTempo) {
      sanitized.globalTempo = Math.max(60, Math.min(200, sanitized.globalTempo));
    }

    return sanitized;
  }
}

