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
