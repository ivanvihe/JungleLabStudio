import { useEffect, useRef, useState } from 'react';

export const useAudioLevel = () => {
  const [enabled, setEnabled] = useState(false);
  const [level, setLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number>();
  const streamRef = useRef<MediaStream | null>(null);

  const refreshDevices = async () => {
    try {
      const mediaDevices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = mediaDevices.filter((device) => device.kind === 'audioinput');
      setDevices(audioInputs);
      if (!selectedDeviceId && audioInputs.length) {
        setSelectedDeviceId(audioInputs[0].deviceId);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const stop = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    analyserRef.current?.disconnect();
    audioContextRef.current?.close();
    audioContextRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setEnabled(false);
  };

  useEffect(() => {
    refreshDevices();
    return () => stop();
  }, []);

  const start = async (deviceId?: string) => {
    try {
      stop();
      const targetDeviceId = deviceId ?? selectedDeviceId ?? undefined;
      const constraints =
        targetDeviceId && targetDeviceId !== 'default'
          ? { deviceId: { exact: targetDeviceId } }
          : undefined;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: constraints ?? true, video: false });
      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.85;
      source.connect(analyser);
      analyserRef.current = analyser;
      streamRef.current = stream;
      await refreshDevices();
      const resolvedId =
        targetDeviceId ?? stream.getAudioTracks()[0]?.getSettings().deviceId ?? selectedDeviceId ?? null;
      setSelectedDeviceId(resolvedId);

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

  const selectDevice = (deviceId: string) => {
    setSelectedDeviceId(deviceId);
    if (enabled) {
      start(deviceId);
    }
  };

  return {
    level,
    enabled,
    error,
    devices,
    selectedDeviceId,
    start,
    stop,
    refreshDevices,
    selectDevice,
  } as const;
};
