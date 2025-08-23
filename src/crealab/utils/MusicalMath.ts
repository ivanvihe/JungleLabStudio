import { Scale, Note } from 'tonal';

// Generate Euclidean rhythm pattern
export function euclideanRhythm(pulses: number, steps: number): boolean[] {
  const pattern: number[] = [];
  const counts: number[] = [];
  const remainders: number[] = [];
  let divisor = steps - pulses;
  let level = 0;

  remainders.push(pulses);
  while (true) {
    counts.push(Math.floor(divisor / remainders[level]));
    remainders.push(divisor % remainders[level]);
    divisor = remainders[level];
    level += 1;
    if (remainders[level] <= 1) break;
  }
  counts.push(divisor);

  const build = (level: number): any => {
    if (level === -1) return [0];
    if (level === -2) return [1];
    const arr = [] as number[];
    const seq = build(level - 1);
    const next = build(level - 2);
    for (let i = 0; i < counts[level]; i++) arr.push(...seq);
    if (remainders[level] !== 0) arr.push(...next);
    return arr;
  };

  const res = build(level);
  for (let i = 0; i < steps; i++) {
    pattern[i] = res[i] === 0;
  }
  return pattern.map(v => !!v);
}

// Get MIDI notes for given key and scale using tonal
export function getScaleNotes(key: string, scale: string): number[] {
  const tonalScale = Scale.get(`${key} ${scale}`);
  return tonalScale.notes.map(n => {
    const midi = Note.midi(n);
    return midi != null ? midi : 60;
  });
}

// Weighted random choice returns index based on weights array
export function weightedRandomChoice(weights: number[]): number {
  const total = weights.reduce((a, b) => a + b, 0);
  let r = Math.random() * total;
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r <= 0) return i;
  }
  return weights.length - 1;
}
