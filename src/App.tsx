import { useEffect, useMemo, useRef, useState } from 'react';
import { ControlPanel } from './components/ControlPanel';
import { useAudioLevel } from './hooks/useAudioLevel';
import { useMidiMapping } from './hooks/useMidiMapping';
import { useP5Sketch } from './hooks/useP5Sketch';
import { presets } from './presets/presets';
import { Parameter, VisualPreset } from './types';

const buildInitialValues = (preset: VisualPreset) =>
  preset.parameters.reduce<Record<string, number>>((acc, param) => {
    acc[param.key] = param.defaultValue;
    return acc;
  }, {});

export default function App() {
  const [presetId, setPresetId] = useState(presets[0].id);
  const [orientation, setOrientation] = useState<'landscape' | 'portrait'>('landscape');
  const currentPreset = useMemo(() => presets.find((p) => p.id === presetId) ?? presets[0], [presetId]);
  const [values, setValues] = useState<Record<string, number>>(buildInitialValues(currentPreset));
  const [midiPulse, setMidiPulse] = useState(0);
  const canvasRef = useRef<HTMLDivElement | null>(null);

  const audio = useAudioLevel();

  const midi = useMidiMapping({
    onValue: (parameterKey, normalizedValue) => {
      const parameter = currentPreset.parameters.find((p) => p.key === parameterKey) as Parameter | undefined;
      if (!parameter) return;
      const mapped = parameter.min + (parameter.max - parameter.min) * normalizedValue;
      setValues((prev) => ({ ...prev, [parameterKey]: mapped }));
    },
    onNote: (note, velocity) => {
      setMidiPulse((prev) => Math.max(prev, velocity));
      const reactiveParam = currentPreset.parameters.find((p) => p.key === 'noteReactive');
      if (reactiveParam) {
        const mapped = reactiveParam.min + (reactiveParam.max - reactiveParam.min) * velocity;
        setValues((prev) => ({ ...prev, noteReactive: mapped, lastNote: note }));
      }
    },
  });

  useEffect(() => {
    if (midiPulse <= 0.001) return;
    const raf = requestAnimationFrame(() => setMidiPulse((prev) => Math.max(0, prev * 0.9 - 0.005)));
    return () => cancelAnimationFrame(raf);
  }, [midiPulse]);

  const handlePresetChange = (id: string) => {
    setPresetId(id);
    const nextPreset = presets.find((p) => p.id === id);
    if (nextPreset) setValues(buildInitialValues(nextPreset));
  };

  const handleChange = (key: string, value: number) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  useP5Sketch(
    currentPreset,
    values,
    audio.level,
    audio.bands,
    audio.beat,
    midiPulse,
    orientation,
    canvasRef,
  );

  return (
    <div className="app">
      <div className={`canvas-shell ${orientation}`} ref={canvasRef}>
        <div className="hint">Soft bloom · neon gradients · audio + MIDI reactive</div>
      </div>
      <ControlPanel
        presets={presets}
        presetId={presetId}
        onPresetChange={handlePresetChange}
        values={values}
        onChange={handleChange}
        midi={midi}
        audio={audio}
        orientation={orientation}
        onOrientationChange={setOrientation}
      />
    </div>
  );
}
