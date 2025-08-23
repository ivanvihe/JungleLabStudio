import { useState, useEffect, useRef } from 'react';
import { AudioData } from '../core/PresetLoader';
import {
  buildLaunchpadFrame,
  LaunchpadPreset,
  isLaunchpadDevice,
  gridIndexToNote,
  canvasToLaunchpadFrame
} from '../utils/launchpad';

export function useLaunchpad(audioData: AudioData, canvasRef: React.RefObject<HTMLCanvasElement>) {
  const launchpadPrevFrameRef = useRef<number[]>(new Array(64).fill(0));

  const [launchpadOutputs, setLaunchpadOutputs] = useState<any[]>([]);
  const [launchpadIdState, setLaunchpadIdState] = useState<string | null>(() => localStorage.getItem('launchpadId'));
  const [launchpadOutput, setLaunchpadOutput] = useState<any | null>(null);
  const [launchpadRunning, setLaunchpadRunning] = useState(false);
  const [launchpadPreset, setLaunchpadPreset] = useState<LaunchpadPreset>('spectrum');
  const [launchpadChannel, setLaunchpadChannel] = useState(() => parseInt(localStorage.getItem('launchpadChannel') || '1'));
  const [launchpadNote, setLaunchpadNote] = useState(() => parseInt(localStorage.getItem('launchpadNote') || '60'));
  const [launchpadSmoothness, setLaunchpadSmoothness] = useState(() => parseFloat(localStorage.getItem('launchpadSmoothness') || '0'));
  const [launchpadText, setLaunchpadText] = useState(() => localStorage.getItem('launchpadText') || 'HELLO');

  const setLaunchpadId = (id: string | null) => {
    setLaunchpadIdState(id);
    if (id) {
      localStorage.setItem('launchpadId', id);
    } else {
      localStorage.removeItem('launchpadId');
    }
  };

  useEffect(() => {
    localStorage.setItem('launchpadChannel', launchpadChannel.toString());
  }, [launchpadChannel]);

  useEffect(() => {
    localStorage.setItem('launchpadNote', launchpadNote.toString());
  }, [launchpadNote]);

  useEffect(() => {
    localStorage.setItem('launchpadSmoothness', launchpadSmoothness.toString());
  }, [launchpadSmoothness]);

  useEffect(() => {
    localStorage.setItem('launchpadText', launchpadText);
  }, [launchpadText]);

  useEffect(() => {
    if (!(navigator as any).requestMIDIAccess) return;
    (navigator as any).requestMIDIAccess({ sysex: true })
      .then((access: any) => {
        const update = () => {
          const outs = Array.from(access.outputs.values()).filter(isLaunchpadDevice);
          setLaunchpadOutputs(outs);
        };
        update();
        access.onstatechange = update;
      })
      .catch((err: any) => console.warn('MIDI access error', err));
  }, []);

  useEffect(() => {
    let lp = launchpadOutputs.find(out => out.id === launchpadIdState) || null;
    if (!lp && launchpadOutputs.length > 0) {
      lp = launchpadOutputs[0];
      setLaunchpadId(lp.id);
    }
    setLaunchpadOutput(lp);
  }, [launchpadOutputs, launchpadIdState]);

  useEffect(() => {
    if (!launchpadRunning || !launchpadOutput) return;
    const rawFrame =
      launchpadPreset === 'canvas'
        ? canvasRef.current
          ? canvasToLaunchpadFrame(canvasRef.current)
          : new Array(64).fill(0)
        : buildLaunchpadFrame(launchpadPreset, audioData, { text: launchpadText });

    if (rawFrame.length !== 64) {
      console.error(`❌ ERROR: buildLaunchpadFrame devolvió ${rawFrame.length} elementos, debería ser 64!`);
      return;
    }

    const prev = launchpadPrevFrameRef.current;
    const alpha = 1 - Math.min(0.99, launchpadSmoothness);
    const frame = rawFrame.map((value, i) => {
      const smoothed = prev[i] + (value - prev[i]) * alpha;
      prev[i] = smoothed;
      return Math.round(smoothed);
    });

    const nonZeroCount = frame.filter(c => c > 0).length;
    console.log(`🎛️ Frame Launchpad: ${nonZeroCount}/64 pads activos, preset: ${launchpadPreset}`);

    frame.forEach((color, i) => {
      const note = gridIndexToNote(i);
      try {
        launchpadOutput.send([0x90, note, color]);
      } catch (e) {
        console.warn(`MIDI send error en pad ${i} (nota ${note}):`, e);
      }
    });
  }, [audioData, launchpadRunning, launchpadPreset, launchpadOutput, launchpadSmoothness, launchpadText, canvasRef]);

  useEffect(() => {
    if (launchpadRunning && launchpadOutput) {
      try {
        console.log('Launchpad: Enviando handshake a', launchpadOutput.name);

        const deviceName = launchpadOutput.name?.toLowerCase() || '';
        if (deviceName.includes('launchpad x')) {
          launchpadOutput.send([0xf0, 0x00, 0x20, 0x29, 0x02, 0x0d, 0x0e, 0x01, 0xf7]);
        } else if (deviceName.includes('launchpad mini mk3')) {
          launchpadOutput.send([0xf0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0e, 0x01, 0xf7]);
        } else if (deviceName.includes('launchpad pro mk3')) {
          launchpadOutput.send([0xf0, 0x00, 0x20, 0x29, 0x02, 0x10, 0x0e, 0x01, 0xf7]);
        } else {
          launchpadOutput.send([0xf0, 0x00, 0x20, 0x29, 0x02, 0x0d, 0x0e, 0x01, 0xf7]);
          launchpadOutput.send([0xf0, 0x00, 0x20, 0x29, 0x02, 0x18, 0x0e, 0x01, 0xf7]);
          launchpadOutput.send([0xf0, 0x00, 0x20, 0x29, 0x02, 0x10, 0x0e, 0x01, 0xf7]);
        }

        for (let i = 0; i < 64; i++) {
          const note = gridIndexToNote(i);
          launchpadOutput.send([0x90, note, 0]);
        }
      } catch (err) {
        console.warn('Error inicializando launchpad:', err);
      }
    } else if (!launchpadRunning && launchpadOutput) {
      try {
        for (let i = 0; i < 64; i++) {
          const note = gridIndexToNote(i);
          launchpadOutput.send([0x90, note, 0]);
        }
      } catch (err) {
        console.warn('Error apagando launchpad:', err);
      }
    }
  }, [launchpadRunning, launchpadOutput]);

  return {
    launchpadOutputs,
    launchpadId: launchpadIdState,
    setLaunchpadId,
    launchpadOutput,
    launchpadRunning,
    setLaunchpadRunning,
    launchpadPreset,
    setLaunchpadPreset,
    launchpadChannel,
    setLaunchpadChannel,
    launchpadNote,
    setLaunchpadNote,
    launchpadSmoothness,
    setLaunchpadSmoothness,
    launchpadText,
    setLaunchpadText,
  };
}

