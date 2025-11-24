import { MutableRefObject, useEffect, useRef } from 'react';
import p5 from 'p5';
import { SketchState, VisualPreset } from '../types';

export const useP5Sketch = (
  preset: VisualPreset | undefined,
  params: Record<string, number>,
  audioLevel: number,
  audioBands: { bass: number; mid: number; treble: number },
  beat: number,
  midiPulse: number,
  midiNote: number,
  midiVelocity: number,
  orientation: 'landscape' | 'portrait',
  containerRef: MutableRefObject<HTMLDivElement | null>,
) => {
  const paramsRef = useRef(params);
  const audioRef = useRef(audioLevel);
  const bandRef = useRef(audioBands);
  const beatRef = useRef(beat);
  const midiRef = useRef(midiPulse);
  const midiNoteRef = useRef(midiNote);
  const midiVelocityRef = useRef(midiVelocity);
  const orientationRef = useRef(orientation);
  paramsRef.current = params;
  audioRef.current = audioLevel;
  bandRef.current = audioBands;
  beatRef.current = beat;
  midiRef.current = midiPulse;
  midiNoteRef.current = midiNote;
  midiVelocityRef.current = midiVelocity;
  orientationRef.current = orientation;

  useEffect(() => {
    if (!preset || !containerRef.current) return;

    const getState = (): SketchState => ({
      params: paramsRef.current,
      audioLevel: audioRef.current,
      audioBands: bandRef.current,
      beat: beatRef.current,
      midiPulse: midiRef.current,
      midiNote: midiNoteRef.current,
      midiVelocity: midiVelocityRef.current,
      orientation: orientationRef.current,
    });

    const container = containerRef.current;
    const instance = new p5((p) => preset.init(p, getState), container);

    const getSize = () => {
      const bounds = container.getBoundingClientRect();
      const width = bounds.width || window.innerWidth;
      const height = bounds.height || window.innerHeight;
      return { width, height };
    };

    const resizeToContainer = () => {
      const { width, height } = getSize();
      if (width > 0 && height > 0) {
        instance.resizeCanvas(width, height, true);
      }
    };

    const originalWindowResized = instance.windowResized?.bind(instance);
    instance.windowResized = () => {
      resizeToContainer();
      originalWindowResized?.();
    };

    resizeToContainer();

    const resizeObserver = new ResizeObserver(() => resizeToContainer());
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      instance.remove();
    };
  }, [preset, containerRef]);
};
