// Simple Euclidean Rhythm implementation
// Based on Bjorklund's algorithm

export function euclideanRhythm(pulses: number, steps: number, offset: number = 0): boolean[] {
  if (pulses >= steps || pulses === 0) {
    return new Array(steps).fill(pulses === steps);
  }

  // Bjorklund's algorithm
  const groups: boolean[][] = [];
  const remainders = [steps - pulses];
  let level = 0;

  // Initialize groups
  for (let i = 0; i < pulses; i++) {
    groups.push([true]);
  }
  for (let i = 0; i < steps - pulses; i++) {
    groups.push([false]);
  }

  while (remainders[level] > 1) {
    const count = remainders[level];
    remainders.push(groups.length - count);
    
    for (let i = 0; i < count; i++) {
      groups[i] = groups[i].concat(groups[groups.length - count + i]);
    }
    
    groups.splice(-count);
    level++;
  }

  // Flatten and apply offset
  let result = groups.flat();
  if (offset > 0) {
    const actualOffset = offset % result.length;
    result = result.slice(-actualOffset).concat(result.slice(0, -actualOffset));
  }
  
  return result;
}

// Patrones específicos para géneros
export const EUCLIDEAN_PATTERNS = {
  kick: {
    minimal: { pulses: 2, steps: 16, offset: 0 },      // [1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]
    dub: { pulses: 3, steps: 8, offset: 0 },           // [1,0,0,1,0,0,1,0]
    hypnotic: { pulses: 7, steps: 16, offset: 3 },     // Desplazado, muy Colin Benders
    fourOnFloor: { pulses: 4, steps: 16, offset: 0 }   // Classic 4/4
  },
  hihat: {
    floating: { pulses: 11, steps: 16, offset: 0 },    // Irregular, Floating Points style
    ambient: { pulses: 5, steps: 13, offset: 7 },      // Odd time, muy experimental
    maxCooper: { pulses: 9, steps: 23, offset: 5 },    // Polimetric complexity
    classic: { pulses: 8, steps: 16, offset: 2 }       // Standard hihat
  },
  bass: {
    dub: { pulses: 4, steps: 15, offset: 1 },          // Slightly off-grid
    minimal: { pulses: 1, steps: 4, offset: 0 },       // One note per bar
    hypnotic: { pulses: 6, steps: 16, offset: 1 },     // 6/16 pattern offset
    syncopated: { pulses: 5, steps: 12, offset: 3 }    // Complex rhythm
  },
  perc: {
    complex: { pulses: 7, steps: 17, offset: 2 },      // Polymetric percussion
    subtle: { pulses: 3, steps: 11, offset: 4 },       // Ambient percussion
    driving: { pulses: 5, steps: 8, offset: 1 }        // Driving rhythm
  }
};

export function generateEuclideanPattern(
  trackType: keyof typeof EUCLIDEAN_PATTERNS,
  style: string
): boolean[] {
  const patterns = EUCLIDEAN_PATTERNS[trackType];
  if (!patterns) {
    return [true, false, false, false];
  }

  const pattern = patterns[style as keyof typeof patterns];
  if (!pattern) {
    const firstStyle = Object.keys(patterns)[0];
    const firstPattern = patterns[firstStyle as keyof typeof patterns];
    return euclideanRhythm(firstPattern.pulses, firstPattern.steps, firstPattern.offset);
  }

  return euclideanRhythm(pattern.pulses, pattern.steps, pattern.offset);
}

export function generateIntelligentPattern(
  trackType: keyof typeof EUCLIDEAN_PATTERNS,
  genre: 'dubTechno' | 'ambient' | 'experimental' | 'hypnotic' = 'dubTechno'
): { pattern: boolean[]; style: string } {
  const genreStyleMappings = {
    dubTechno: {
      kick: 'dub',
      bass: 'dub',
      hihat: 'floating',
      perc: 'subtle'
    },
    ambient: {
      kick: 'minimal',
      bass: 'minimal',
      hihat: 'ambient',
      perc: 'subtle'
    },
    experimental: {
      kick: 'hypnotic',
      bass: 'syncopated',
      hihat: 'maxCooper',
      perc: 'complex'
    },
    hypnotic: {
      kick: 'hypnotic',
      bass: 'hypnotic',
      hihat: 'floating',
      perc: 'driving'
    }
  } as const;

  const style =
    genreStyleMappings[genre][trackType] ||
    Object.keys(EUCLIDEAN_PATTERNS[trackType])[0];
  const pattern = generateEuclideanPattern(trackType, style);
  return { pattern, style };
}
