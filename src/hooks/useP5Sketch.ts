import { MutableRefObject, useEffect, useRef } from 'react';
import p5 from 'p5';
import { SketchState, VisualPreset } from '../types';

export const useP5Sketch = (
  preset: VisualPreset | undefined,
  params: Record<string, number>,
  audioLevel: number,
  containerRef: MutableRefObject<HTMLDivElement | null>,
) => {
  const paramsRef = useRef(params);
  const audioRef = useRef(audioLevel);
  paramsRef.current = params;
  audioRef.current = audioLevel;

  useEffect(() => {
    if (!preset || !containerRef.current) return;

    const getState = (): SketchState => ({
      params: paramsRef.current,
      audioLevel: audioRef.current,
    });

    const instance = new p5((p) => preset.init(p, getState), containerRef.current);

    return () => {
      instance.remove();
    };
  }, [preset, containerRef]);
};
