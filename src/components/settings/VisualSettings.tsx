import React from 'react';

interface VisualSettingsProps {
  hideUiHotkey: string;
  onHideUiHotkeyChange: (value: string) => void;
  fullscreenHotkey: string;
  onFullscreenHotkeyChange: (value: string) => void;
  exitFullscreenHotkey: string;
  onExitFullscreenHotkeyChange: (value: string) => void;
  fullscreenByDefault: boolean;
  onFullscreenByDefaultChange: (value: boolean) => void;
  canvasBrightness: number;
  onCanvasBrightnessChange: (value: number) => void;
  canvasVibrance: number;
  onCanvasVibranceChange: (value: number) => void;
  canvasBackground: string;
  onCanvasBackgroundChange: (value: string) => void;
  glitchTextPads: number;
  onGlitchPadChange: (value: number) => void;
}

export const VisualSettings: React.FC<VisualSettingsProps> = ({
  hideUiHotkey,
  onHideUiHotkeyChange,
  fullscreenHotkey,
  onFullscreenHotkeyChange,
  exitFullscreenHotkey,
  onExitFullscreenHotkeyChange,
  fullscreenByDefault,
  onFullscreenByDefaultChange,
  canvasBrightness,
  onCanvasBrightnessChange,
  canvasVibrance,
  onCanvasVibranceChange,
  canvasBackground,
  onCanvasBackgroundChange,
  glitchTextPads,
  onGlitchPadChange,
}) => {
  return (
    <div className="settings-section">
      <h3>🎨 Configuración Visual</h3>
      <div className="setting-group">
        <label className="setting-label">
          <span>Tecla para ocultar UI</span>
          <input
            type="text"
            value={hideUiHotkey}
            onKeyDown={(e) => {
              e.preventDefault();
              onHideUiHotkeyChange(e.key);
            }}
            className="setting-number"
            readOnly
          />
        </label>
        <small className="setting-hint">Presiona una tecla (por defecto F10)</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Tecla para fullscreen</span>
          <input
            type="text"
            value={fullscreenHotkey}
            onKeyDown={(e) => {
              e.preventDefault();
              onFullscreenHotkeyChange(e.key);
            }}
            className="setting-number"
            readOnly
          />
        </label>
        <small className="setting-hint">Presiona una tecla (por defecto F9)</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Tecla para salir de fullscreen</span>
          <input
            type="text"
            value={exitFullscreenHotkey}
            onKeyDown={(e) => {
              e.preventDefault();
              onExitFullscreenHotkeyChange(e.key);
            }}
            className="setting-number"
            readOnly
          />
        </label>
        <small className="setting-hint">Presiona una tecla (por defecto F11)</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <input
            type="checkbox"
            checked={fullscreenByDefault}
            onChange={(e) => onFullscreenByDefaultChange(e.target.checked)}
          />
          <span>Ventanas en fullscreen por defecto</span>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Brillo: {canvasBrightness.toFixed(2)}</span>
          <input
            type="range"
            min={0.5}
            max={2}
            step={0.1}
            value={canvasBrightness}
            onChange={(e) => onCanvasBrightnessChange(parseFloat(e.target.value))}
            className="setting-slider"
          />
        </label>
        <small className="setting-hint">Ajusta el brillo global del canvas</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Viveza: {canvasVibrance.toFixed(2)}</span>
          <input
            type="range"
            min={0}
            max={2}
            step={0.1}
            value={canvasVibrance}
            onChange={(e) => onCanvasVibranceChange(parseFloat(e.target.value))}
            className="setting-slider"
          />
        </label>
        <small className="setting-hint">Acentúa los valores de brillo</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Color de fondo del canvas</span>
          <input
            type="color"
            value={canvasBackground}
            onChange={(e) => onCanvasBackgroundChange(e.target.value)}
            className="setting-color"
          />
        </label>
        <small className="setting-hint">Elige un color de fondo para el canvas</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Pads de Texto Glitch: {glitchTextPads}</span>
          <input
            type="range"
            min={1}
            max={8}
            step={1}
            value={glitchTextPads}
            onChange={(e) => onGlitchPadChange(parseInt(e.target.value))}
            className="setting-slider"
          />
        </label>
        <small className="setting-hint">Número de pads de texto disponibles en presets de glitch</small>
      </div>

      <div className="setting-group">
        <h4>Configuración de Layers</h4>
        <div className="layers-info">
          <div className="layer-info">
            <span className="layer-badge layer-c">C</span>
            <span>Layer de Fondo - Renderiza primero</span>
          </div>
          <div className="layer-info">
            <span className="layer-badge layer-b">B</span>
            <span>Layer Medio - Mezcla con transparencia</span>
          </div>
          <div className="layer-info">
            <span className="layer-badge layer-a">A</span>
            <span>Layer Frontal - Renderiza encima</span>
          </div>
        </div>
        <small className="setting-hint">
          Todos los layers se mezclan con transparencia automática. Los presets mantienen fondos transparentes para permitir la composición correcta.
        </small>
      </div>

      <div className="setting-group">
        <h4>Calidad Visual</h4>
        <div className="quality-presets">
          <button
            className="quality-button"
            onClick={() => {
              onCanvasBrightnessChange(1);
              onCanvasVibranceChange(1);
            }}
          >
            🏃 Rendimiento
          </button>
          <button
            className="quality-button"
            onClick={() => {
              onCanvasBrightnessChange(1);
              onCanvasVibranceChange(1);
            }}
          >
            ⚖️ Balanceado
          </button>
          <button
            className="quality-button"
            onClick={() => {
              onCanvasBrightnessChange(1.5);
              onCanvasVibranceChange(1.5);
            }}
          >
            💎 Calidad
          </button>
        </div>
      </div>
    </div>
  );
};

