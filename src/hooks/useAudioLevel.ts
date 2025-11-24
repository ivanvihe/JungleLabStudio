import { useEffect, useRef, useState } from 'react';

export const useAudioLevel = () => {
  const [enabled, setEnabled] = useState(false);
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number>();
  const streamRef = useRef<MediaStream | null>(null);

  const stop = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    analyserRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setEnabled(false);
  };

  useEffect(() => () => stop(), []);

  const start = async () => {
    try {
      if (enabled) return;
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.85;
      source.connect(analyser);
      analyserRef.current = analyser;
      streamRef.current = stream;

      const buffer = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteTimeDomainData(buffer);
        let sum = 0;
        for (let i = 0; i < buffer.length; i += 1) {
          const centered = buffer[i] / 128 - 1;
          sum += centered * centered;
        }
        const rms = Math.sqrt(sum / buffer.length);
        setLevel(Math.min(1, rms * 1.6));
        rafRef.current = requestAnimationFrame(tick);
      };

      tick();
      setEnabled(true);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('No se pudo habilitar el micrófono. Verifica permisos.');
    }
  };

  return { level, enabled, error, start, stop } as const;
};
