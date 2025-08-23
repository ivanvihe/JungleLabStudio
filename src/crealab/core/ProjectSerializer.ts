import { CreaLabProject, GenerativeTrack, ProjectExportFormat, TrackType } from '../types/CrealabTypes';
import { JsonValidator } from '../utils/JsonValidator';

export interface SerializedProject {
  version: string;
  timestamp: string;
  metadata: {
    exportedBy: string;
    creaLabVersion: string;
    platform: string;
  };
  project: CreaLabProject;
}

export class ProjectSerializer {
  private static readonly CURRENT_VERSION = '2.0.0';
  private static readonly CREALAB_VERSION = '1.0.0';

  // Serializar proyecto completo a JSON
  static serialize(project: CreaLabProject): string {
    const serialized: SerializedProject = {
      version: this.CURRENT_VERSION,
      timestamp: new Date().toISOString(),
      metadata: {
        exportedBy: 'Jungle Lab Studio - Crea Lab',
        creaLabVersion: this.CREALAB_VERSION,
        platform: (typeof navigator !== 'undefined' && navigator.platform) ? navigator.platform : 'Unknown'
      },
      project: this.cleanProjectForExport(project)
    };

    return JSON.stringify(serialized, null, 2);
  }

  // Deserializar proyecto desde JSON
  static deserialize(jsonString: string): CreaLabProject {
    try {
      const data = JSON.parse(jsonString);

      // Validar estructura básica
      if (!data.project) {
        throw new Error('Invalid project file: missing project data');
      }

      // Validar con JsonValidator
      const validationResult = JsonValidator.validateProject(data.project);
      if (!validationResult.valid) {
        console.warn('Project validation warnings:', validationResult.errors);
      }

      // Migrar desde versiones anteriores si es necesario
      const migratedProject = this.migrateProject(data);

      // Limpiar y normalizar
      return this.normalizeProject(migratedProject.project);

    } catch (error: any) {
      console.error('Failed to deserialize project:', error);
      throw new Error(`Project deserialization failed: ${error.message}`);
    }
  }

  // Limpiar proyecto para export (remover datos temporales)
  private static cleanProjectForExport(project: CreaLabProject): CreaLabProject {
    const cleaned = JSON.parse(JSON.stringify(project));

    // Limpiar datos temporales de transport
    cleaned.transport = {
      ...cleaned.transport,
      isPlaying: false,
      isPaused: false,
      currentBeat: 0,
      currentBar: 0,
      currentStep: 0
    };

    // Limpiar estado de generadores
    cleaned.tracks = cleaned.tracks.map((track: GenerativeTrack) => ({
      ...track,
      generator: {
        ...track.generator,
        lastNoteTime: 0,
        currentStep: 0
      },
      controls: {
        ...track.controls,
        playStop: false // Resetear estados de play
      }
    }));

    // Remover datos legacy si existen
    delete (cleaned as any).scenes;
    delete (cleaned as any).oldTracks;

    return cleaned;
  }

  // Migrar desde versiones anteriores
  private static migrateProject(data: any): SerializedProject {
    const version = data.version || '1.0.0';

    console.log(`🔄 Migrating project from version ${version} to ${this.CURRENT_VERSION}`);

    switch (version) {
      case '1.0.0':
        return this.migrateFromV1(data);
      case '2.0.0':
        return data as SerializedProject;
      default:
        console.warn(`Unknown project version: ${version}. Attempting migration...`);
        return this.migrateFromV1(data);
    }
  }

  // Migración desde v1.0.0 (clips system) a v2.0.0 (generative system)
  private static migrateFromV1(data: any): SerializedProject {
    const oldProject = data.project || data;

    // Crear estructura nueva
    const migratedProject: CreaLabProject = {
      id: oldProject.id || `migrated-${Date.now()}`,
      name: oldProject.name || 'Migrated Project',
      description: 'Migrated from legacy clip-based system',

      // Crear 8 tracks fijos desde tracks antiguos
      tracks: this.createFixedTracksFromLegacy(oldProject.tracks || []),

      globalTempo: oldProject.globalTempo || 128,
      key: oldProject.key || 'C',
      scale: oldProject.scale || 'minor',
      genre: 'Techno', // Default para migración

      transport: {
        isPlaying: false,
        isPaused: false,
        currentBeat: 0,
        currentBar: 0,
        currentStep: 0
      },

      launchControl: {
        connected: false
      },

      midiClock: {
        enabled: false,
        source: 'internal',
        ppqn: 24
      }
    };

    return {
      version: this.CURRENT_VERSION,
      timestamp: new Date().toISOString(),
      metadata: {
        exportedBy: 'Jungle Lab Studio - Crea Lab (Migration)',
        creaLabVersion: this.CREALAB_VERSION,
        platform: (typeof navigator !== 'undefined' && navigator.platform) ? navigator.platform : 'Unknown'
      },
      project: migratedProject
    };
  }

  // Crear 8 tracks fijos desde sistema legacy
  private static createFixedTracksFromLegacy(legacyTracks: any[]): [
    GenerativeTrack, GenerativeTrack, GenerativeTrack, GenerativeTrack,
    GenerativeTrack, GenerativeTrack, GenerativeTrack, GenerativeTrack
  ] {
    const fixedTracks: GenerativeTrack[] = [];

    for (let i = 1; i <= 8; i++) {
      const legacyTrack = legacyTracks[i - 1];

      const track: GenerativeTrack = {
        id: `track-${i}`,
        name: legacyTrack?.name || `Track ${i}`,
        trackNumber: i,
        color: `hsl(${(i - 1) * 45}, 70%, 60%)`,
        trackType: (legacyTrack?.trackType || 'bass') as TrackType,

        outputDevice: legacyTrack?.midiDevice || '',
        midiChannel: legacyTrack?.midiChannel || i,

        generator: {
          type: 'off', // Migrar como desactivado inicialmente
          enabled: false,
          parameters: {},
          lastNoteTime: 0,
          currentStep: 0
        },

        controls: {
          intensity: 64,
          paramA: 64,
          paramB: 64,
          paramC: 64,
          playStop: false,
          mode: 0
        },

        launchControlMapping: {
          stripNumber: i,
          faderCC: 77 + (i - 1),
          knob1CC: 13 + (i - 1) * 4,
          knob2CC: 14 + (i - 1) * 4,
          knob3CC: 15 + (i - 1) * 4,
          button1CC: 41 + (i - 1),
          button2CC: 57 + (i - 1)
        }
      };

      fixedTracks.push(track);
    }

    return fixedTracks as [
      GenerativeTrack, GenerativeTrack, GenerativeTrack, GenerativeTrack,
      GenerativeTrack, GenerativeTrack, GenerativeTrack, GenerativeTrack
    ];
  }

  // Normalizar proyecto después de deserialización
  private static normalizeProject(project: CreaLabProject): CreaLabProject {
    // Asegurar que tiene todos los campos requeridos
    return {
      ...project,
      description: project.description || '',
      genre: project.genre || 'Techno',
      transport: project.transport || {
        isPlaying: false,
        isPaused: false,
        currentBeat: 0,
        currentBar: 0,
        currentStep: 0
      },
      launchControl: project.launchControl || {
        connected: false
      },
      midiClock: project.midiClock || {
        enabled: false,
        source: 'internal',
        ppqn: 24
      }
    };
  }

  // Exportar en diferentes formatos
  static exportProject(project: CreaLabProject, format: ProjectExportFormat): string {
    switch (format) {
      case 'json':
        return this.serialize(project);
      case 'preset':
        return this.exportAsPreset(project);
      case 'ableton':
        return this.exportForAbleton(project);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  // Exportar como preset (solo configuración de generadores)
  private static exportAsPreset(project: CreaLabProject): string {
    const preset = {
      name: project.name,
      genre: project.genre,
      key: project.key,
      scale: project.scale,
      tempo: project.globalTempo,
      tracks: project.tracks.map(track => ({
        name: track.name,
        instrumentProfile: track.instrumentProfile,
        generator: track.generator,
        color: track.color
      }))
    };

    return JSON.stringify(preset, null, 2);
  }

  // Exportar para Ableton Live
  private static exportForAbleton(project: CreaLabProject): string {
    let output = `# Ableton Live Session Export\n`;
    output += `# Project: ${project.name}\n`;
    output += `# Tempo: ${project.globalTempo} BPM\n`;
    output += `# Key: ${project.key} ${project.scale}\n\n`;

    project.tracks.forEach(track => {
      if (track.generator.enabled) {
        output += `## Track ${track.trackNumber}: ${track.name}\n`;
        output += `MIDI Channel: ${track.midiChannel}\n`;
        output += `Generator: ${track.generator.type}\n`;
        output += `Parameters: ${JSON.stringify(track.generator.parameters)}\n\n`;
      }
    });

    return output;
  }

  // Crear backup automático
  static createBackup(project: CreaLabProject): void {
    const backupKey = `crealab_backup_${Date.now()}`;
    const backup = this.serialize(project);

    try {
      // Mantener solo los últimos 5 backups
      const existingBackups = Object.keys(localStorage)
        .filter(key => key.startsWith('crealab_backup_'))
        .sort()
        .reverse();

      if (existingBackups.length >= 5) {
        existingBackups.slice(5).forEach(key => {
          localStorage.removeItem(key);
        });
      }

      localStorage.setItem(backupKey, backup);
      console.log('📋 Project backup created:', backupKey);

    } catch (error) {
      console.warn('Failed to create backup:', error);
    }
  }

  // Recuperar backups disponibles
  static getAvailableBackups(): { key: string; timestamp: Date; name: string }[] {
    const backups: { key: string; timestamp: Date; name: string }[] = [];

    Object.keys(localStorage)
      .filter(key => key.startsWith('crealab_backup_'))
      .forEach(key => {
        try {
          const data = JSON.parse(localStorage.getItem(key) || '');
          const timestamp = new Date(data.timestamp);
          const name = data.project?.name || 'Unknown Project';

          backups.push({ key, timestamp, name });
        } catch (error) {
          console.warn(`Invalid backup: ${key}`);
        }
      });

    return backups.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  // Recuperar backup específico
  static restoreBackup(backupKey: string): CreaLabProject {
    const backup = localStorage.getItem(backupKey);
    if (!backup) {
      throw new Error('Backup not found');
    }

    return this.deserialize(backup);
  }
}

