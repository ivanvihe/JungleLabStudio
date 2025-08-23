import React, { useState, useEffect } from 'react';

interface DeviceOption {
  id: string;
  label: string;
}

interface AudioSettingsProps {
  audioDevices: DeviceOption[];
  selectedAudioId: string | null;
  onSelectAudio: (id: string) => void;
  audioGain: number;
  onAudioGainChange: (value: number) => void;
}

export const AudioSettings: React.FC<AudioSettingsProps> = ({
  audioDevices,
  selectedAudioId,
  onSelectAudio,
  audioGain,
  onAudioGainChange
}) => {
  const [bufferSize, setBufferSize] = useState(() =>
    parseInt(localStorage.getItem('audioBufferSize') || '2048')
  );
  const [fftSize, setFFTSize] = useState(() =>
    parseInt(localStorage.getItem('fftSize') || '2048')
  );
  const [smoothingTime, setSmoothingTime] = useState(() =>
    parseFloat(localStorage.getItem('audioSmoothing') || '0.8')
  );

  useEffect(() => {
    localStorage.setItem('audioBufferSize', bufferSize.toString());
  }, [bufferSize]);

  useEffect(() => {
    localStorage.setItem('fftSize', fftSize.toString());
  }, [fftSize]);

  useEffect(() => {
    localStorage.setItem('audioSmoothing', smoothingTime.toString());
  }, [smoothingTime]);

  return (
    <div className="settings-section">
      <h3>🎵 Configuración de Audio</h3>

      <div className="setting-group">
        <label className="setting-label">
          <span>Dispositivo de Entrada</span>
          <select
            value={selectedAudioId || ''}
            onChange={(e) => onSelectAudio(e.target.value)}
            className="setting-select"
          >
            <option value="">Por Defecto</option>
            {audioDevices.map((dev) => (
              <option key={dev.id} value={dev.id}>
                {dev.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Ganancia de Entrada: {(audioGain * 100).toFixed(0)}%</span>
          <input
            type="range"
            min={0}
            max={2}
            step={0.01}
            value={audioGain}
            onChange={(e) => onAudioGainChange(parseFloat(e.target.value))}
            className="setting-slider"
          />
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Tamaño de Buffer</span>
          <select
            value={bufferSize}
            onChange={(e) => setBufferSize(parseInt(e.target.value))}
            className="setting-select"
          >
            <option value={512}>512 (Baja latencia)</option>
            <option value={1024}>1024 (Balanceado)</option>
            <option value={2048}>2048 (Recomendado)</option>
            <option value={4096}>4096 (Alta estabilidad)</option>
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Resolución FFT</span>
          <select
            value={fftSize}
            onChange={(e) => setFFTSize(parseInt(e.target.value))}
            className="setting-select"
          >
            <option value={1024}>1024 (Rápido)</option>
            <option value={2048}>2048 (Recomendado)</option>
            <option value={4096}>4096 (Alta precisión)</option>
            <option value={8192}>8192 (Máxima calidad)</option>
          </select>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Suavizado de Audio: {(smoothingTime * 100).toFixed(0)}%</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={smoothingTime}
            onChange={(e) => setSmoothingTime(parseFloat(e.target.value))}
            className="setting-slider"
          />
        </label>
      </div>
    </div>
  );
};

