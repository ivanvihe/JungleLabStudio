import { MidiClip, Scene } from '../types/CrealabTypes';

export class MidiExporter {
  static exportSceneToText(scene: Scene): string {
    let output = `# Scene: ${scene.name}\n`;
    output += `# Duration: ${scene.duration} bars\n`;
    output += `# Tempo: ${scene.tempo} BPM\n\n`;
    
    scene.clips.forEach(clip => {
      if (clip.enabled && clip.notes.length > 0) {
        output += `## Track: ${clip.name} (Channel ${clip.channel})\n`;
        clip.notes.forEach(note => {
          output += `Note ${note.note}, Time: ${note.time.toFixed(2)}, Vel: ${note.velocity}, Dur: ${note.duration}\n`;
        });
        output += '\n';
      }
    });
    
    return output;
  }

  static exportClipToJSON(clip: MidiClip): string {
    const exportData = {
      name: clip.name,
      trackType: clip.trackType,
      channel: clip.channel,
      duration: clip.duration,
      notes: clip.notes.map(note => ({
        note: note.note,
        time: note.time,
        velocity: note.velocity,
        duration: note.duration
      }))
    };
    
    return JSON.stringify(exportData, null, 2);
  }

  static exportSceneToAbleton(scene: Scene): string {
    let output = `# Ableton Live Session Export\n`;
    output += `# Import instructions: Create MIDI tracks and import each section\n\n`;
    
    // Group by track type
    const trackGroups: Record<string, MidiClip[]> = {};
    scene.clips.forEach(clip => {
      if (clip.enabled) {
        if (!trackGroups[clip.trackType]) {
          trackGroups[clip.trackType] = [];
        }
        trackGroups[clip.trackType].push(clip);
      }
    });
    
    Object.entries(trackGroups).forEach(([trackType, clips]) => {
      output += `## ${trackType.toUpperCase()} TRACK (Create new MIDI track)\n`;
      clips.forEach((clip, index) => {
        output += `### Clip ${index + 1}: ${clip.name}\n`;
        output += `Channel: ${clip.channel}\n`;
        output += `Notes:\n`;
        clip.notes.forEach(note => {
          const bars = Math.floor(note.time / 4);
          const beats = ((note.time % 4) + 1).toFixed(2);
          output += `  ${bars}:${beats} - Note ${note.note} (Vel: ${note.velocity})\n`;
        });
        output += '\n';
      });
    });
    
    return output;
  }

  static downloadAsFile(content: string, filename: string, type: string = 'text/plain') {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
  }

  static exportSceneForAudioVisualizer(scene: Scene): any {
    // This will be implemented later for visual integration
    return { scene: scene.name, clips: scene.clips.length };
  }
}

