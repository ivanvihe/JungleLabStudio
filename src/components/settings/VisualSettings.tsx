import React from 'react';
import { TouchDesignerSettings } from '../../types/touchDesigner';

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
  touchDesignerSettings: TouchDesignerSettings;
  onTouchDesignerSettingsChange: (settings: Partial<TouchDesignerSettings>) => void;
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
  touchDesignerSettings,
  onTouchDesignerSettingsChange,
}) => {
  return (
    <div className="settings-section">
      <h3>🎨 Visual Settings</h3>
      <div className="setting-group">
        <label className="setting-label">
          <span>Hide UI Hotkey</span>
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
        <small className="setting-hint">Press a key (default F10)</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Fullscreen Hotkey</span>
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
        <small className="setting-hint">Press a key (default F9)</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Exit Fullscreen Hotkey</span>
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
        <small className="setting-hint">Press a key (default F11)</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <input
            type="checkbox"
            checked={fullscreenByDefault}
            onChange={(e) => onFullscreenByDefaultChange(e.target.checked)}
          />
          <span>Open windows in fullscreen by default</span>
        </label>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Brightness: {canvasBrightness.toFixed(2)}</span>
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
        <small className="setting-hint">Adjust overall canvas brightness</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Vibrance: {canvasVibrance.toFixed(2)}</span>
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
        <small className="setting-hint">Accentuates brightness values</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <span>Canvas background color</span>
          <input
            type="color"
            value={canvasBackground}
            onChange={(e) => onCanvasBackgroundChange(e.target.value)}
            className="setting-color"
          />
        </label>
        <small className="setting-hint">Choose a canvas background color</small>
      </div>

      <div className="setting-group">
        <label className="setting-label">
          <input
            type="checkbox"
            checked={touchDesignerSettings.enabled}
            onChange={(e) => onTouchDesignerSettingsChange({ enabled: e.target.checked })}
          />
          <span>TouchDesigner mode (calidad cinematográfica)</span>
        </label>
        <small className="setting-hint">
          Activa un pipeline de post-procesado tipo TouchDesigner con bloom, aberración y viñeteado.
        </small>
      </div>

      {touchDesignerSettings.enabled && (
        <div className="setting-group">
          <h4>Profiling pro</h4>
          <div className="quality-presets">
            <button
              className="quality-button"
              onClick={() =>
                onTouchDesignerSettingsChange({
                  bloomStrength: 0.65,
                  bloomRadius: 0.2,
                  bloomThreshold: 0.22,
                  filmGrain: 0.15,
                  chromaticAberration: 0.0008,
                  vignetteDarkness: 0.5,
                  exposure: 1.05,
                })
              }
            >
              🏃 Directo
            </button>
            <button
              className="quality-button"
              onClick={() =>
                onTouchDesignerSettingsChange({
                  bloomStrength: 0.9,
                  bloomRadius: 0.35,
                  bloomThreshold: 0.18,
                  filmGrain: 0.25,
                  chromaticAberration: 0.0011,
                  vignetteDarkness: 0.65,
                  exposure: 1.12,
                })
              }
            >
              ⚖️ Balanceado
            </button>
            <button
              className="quality-button"
              onClick={() =>
                onTouchDesignerSettingsChange({
                  bloomStrength: 1.35,
                  bloomRadius: 0.48,
                  bloomThreshold: 0.12,
                  filmGrain: 0.38,
                  chromaticAberration: 0.0018,
                  vignetteDarkness: 0.8,
                  exposure: 1.25,
                })
              }
            >
              💎 Cinema / TD
            </button>
          </div>

          <label className="setting-label">
            <span>Bloom strength: {touchDesignerSettings.bloomStrength.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={2}
              step={0.01}
              value={touchDesignerSettings.bloomStrength}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ bloomStrength: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>
          <label className="setting-label">
            <span>Bloom radius: {touchDesignerSettings.bloomRadius.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={touchDesignerSettings.bloomRadius}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ bloomRadius: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>
          <label className="setting-label">
            <span>Bloom umbral: {touchDesignerSettings.bloomThreshold.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={touchDesignerSettings.bloomThreshold}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ bloomThreshold: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>

          <label className="setting-label">
            <span>Grano cine: {touchDesignerSettings.filmGrain.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={touchDesignerSettings.filmGrain}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ filmGrain: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>

          <label className="setting-label">
            <span>Aberración RGB: {touchDesignerSettings.chromaticAberration.toFixed(4)}</span>
            <input
              type="range"
              min={0}
              max={0.003}
              step={0.0001}
              value={touchDesignerSettings.chromaticAberration}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ chromaticAberration: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>

          <label className="setting-label">
            <span>Viñeta: {touchDesignerSettings.vignetteDarkness.toFixed(2)}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={touchDesignerSettings.vignetteDarkness}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ vignetteDarkness: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>

          <label className="setting-label">
            <span>Exposición: {touchDesignerSettings.exposure.toFixed(2)}</span>
            <input
              type="range"
              min={0.6}
              max={1.6}
              step={0.01}
              value={touchDesignerSettings.exposure}
              onChange={(e) =>
                onTouchDesignerSettingsChange({ exposure: parseFloat(e.target.value) })
              }
              className="setting-slider"
            />
          </label>
        </div>
      )}

      <div className="setting-group">
        <label className="setting-label">
          <span>Glitch Text Pads: {glitchTextPads}</span>
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
        <small className="setting-hint">Number of text pads available in glitch presets</small>
      </div>

      <div className="setting-group">
        <h4>Layer Settings</h4>
        <div className="layers-info">
          <div className="layer-info">
            <span className="layer-badge layer-c">C</span>
            <span>Background Layer - renders first</span>
          </div>
          <div className="layer-info">
            <span className="layer-badge layer-b">B</span>
            <span>Middle Layer - blends with transparency</span>
          </div>
          <div className="layer-info">
            <span className="layer-badge layer-a">A</span>
            <span>Front Layer - renders on top</span>
          </div>
        </div>
        <small className="setting-hint">
          All layers are blended with automatic transparency. Presets keep transparent backgrounds to allow correct compositing.
        </small>
      </div>

      <div className="setting-group">
        <h4>Visual Quality</h4>
        <div className="quality-presets">
          <button
            className="quality-button"
            onClick={() => {
              onCanvasBrightnessChange(1);
              onCanvasVibranceChange(1);
            }}
          >
            🏃 Performance
          </button>
          <button
            className="quality-button"
            onClick={() => {
              onCanvasBrightnessChange(1);
              onCanvasVibranceChange(1);
            }}
          >
            ⚖️ Balanced
          </button>
          <button
            className="quality-button"
            onClick={() => {
              onCanvasBrightnessChange(1.5);
              onCanvasVibranceChange(1.5);
            }}
          >
            💎 Quality
          </button>
        </div>
      </div>
    </div>
  );
};

