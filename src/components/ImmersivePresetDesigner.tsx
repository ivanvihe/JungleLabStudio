import React, { useState, useEffect } from 'react';
import { LoadedPreset } from '../core/PresetLoader';
import { useMidiContext } from '../contexts/MidiContext';
import './ImmersivePresetDesigner.css';

export interface ImmersiveTemplate {
  id: string;
  name: string;
  basePresetId: string;
  palettes: string[];
  volumetric: boolean;
  particles: 'delicate' | 'cinematic' | 'dense';
  turbulence: number;
  glow: number;
  motion: number;
  notes: string;
  audioReactive: {
    density: boolean;
    glow: boolean;
    color: boolean;
  };
}

interface ImmersivePresetDesignerProps {
  isOpen: boolean;
  onClose: () => void;
  presets: LoadedPreset[];
  templates: ImmersiveTemplate[];
  onSaveTemplate: (template: ImmersiveTemplate) => void;
}

const COLOR_OPTIONS = [
  'cyan',
  'turquoise',
  'magenta',
  'fuchsia',
  'purple',
  'electric blue',
  'green',
  'warm yellow',
];

export const ImmersivePresetDesigner: React.FC<ImmersivePresetDesignerProps> = ({
  isOpen,
  onClose,
  presets,
  templates,
  onSaveTemplate,
}) => {
  const [draft, setDraft] = useState<ImmersiveTemplate>(() => ({
    id: `draft-${Date.now()}`,
    name: 'Immersive preset',
    basePresetId: presets[0]?.id || '',
    palettes: ['cyan', 'magenta', 'purple'],
    volumetric: true,
    particles: 'cinematic',
    turbulence: 0.6,
    glow: 0.5,
    motion: 0.5,
    notes: 'Capas holográficas + luz volumétrica + movimiento orgánico.',
    audioReactive: { density: true, glow: true, color: false },
  }));

  const { startParameterLearn, cancelParameterLearn, parameterLearnTarget, parameterMappings, mappedParameterEvent, clearParameterMapping } = useMidiContext();

  useEffect(() => {
    if (!mappedParameterEvent) return;
    const [, , paramKey] = mappedParameterEvent.target.split(':');
    if (paramKey && ['glow', 'turbulence', 'motion'].includes(paramKey)) {
      setDraft(prev => ({ ...prev, [paramKey]: mappedParameterEvent.value }));
    }
  }, [mappedParameterEvent]);

  const togglePalette = (color: string) => {
    setDraft(prev => {
      const hasColor = prev.palettes.includes(color);
      const palettes = hasColor
        ? prev.palettes.filter(c => c !== color)
        : [...prev.palettes, color];
      return { ...prev, palettes };
    });
  };

  const save = () => {
    if (!draft.name.trim() || !draft.basePresetId) return;
    onSaveTemplate({ ...draft, id: `template-${Date.now()}` });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="designer-overlay" onClick={onClose}>
      <div className="designer-modal" onClick={e => e.stopPropagation()}>
        <div className="designer-header">
          <div>
            <h2>Immersive Preset Designer</h2>
            <p>Crea presets cinematográficos con controles MIDI y guías artísticas.</p>
          </div>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="designer-grid">
          <section className="designer-card">
            <h3>Esqueleto del preset</h3>
            <label className="field">
              <span>Nombre</span>
              <input
                value={draft.name}
                onChange={e => setDraft(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Nombre cinematográfico"
              />
            </label>
            <label className="field">
              <span>Preset base</span>
              <select
                value={draft.basePresetId}
                onChange={e => setDraft(prev => ({ ...prev, basePresetId: e.target.value }))}
              >
                {presets.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.config.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Notas de atmósfera</span>
              <textarea
                value={draft.notes}
                rows={3}
                onChange={e => setDraft(prev => ({ ...prev, notes: e.target.value }))}
              />
            </label>
            <div className="palette-grid">
              {COLOR_OPTIONS.map(color => (
                <button
                  key={color}
                  className={`palette-chip ${draft.palettes.includes(color) ? 'active' : ''}`}
                  onClick={() => togglePalette(color)}
                  type="button"
                >
                  {color}
                </button>
              ))}
            </div>
          </section>

          <section className="designer-card">
            <h3>Motion & depth</h3>
            <div className="slider-row">
              <label>Partículas</label>
              <div className="chip-row">
                {['delicate', 'cinematic', 'dense'].map(opt => (
                  <button
                    key={opt}
                    type="button"
                    className={`chip ${draft.particles === opt ? 'active' : ''}`}
                    onClick={() => setDraft(prev => ({ ...prev, particles: opt as ImmersiveTemplate['particles'] }))}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
            <div className="slider-row">
              <label>Volumetría</label>
              <div className="toggle">
                <input
                  type="checkbox"
                  checked={draft.volumetric}
                  onChange={e => setDraft(prev => ({ ...prev, volumetric: e.target.checked }))}
                />
                <span>Niebla holográfica + halos suaves</span>
              </div>
            </div>
            {['glow', 'turbulence', 'motion'].map(key => (
              <div className="slider-row" key={key}>
                <div className="slider-label">
                  <label>{key === 'glow' ? 'Brillo Cinemático' : key === 'turbulence' ? 'Ruido / Curl' : 'Velocidad orgánica'}</label>
                  <div className="midi-inline">
                    <button
                      type="button"
                      className={`midi-learn ${parameterLearnTarget?.id === `designer:${key}` ? 'learning' : ''}`}
                      onClick={() =>
                        parameterLearnTarget?.id === `designer:${key}`
                          ? cancelParameterLearn()
                          : startParameterLearn(`designer:${key}`, { min: 0, max: 1, label: key })
                      }
                    >
                      {parameterLearnTarget?.id === `designer:${key}` ? 'Asignando…' : 'Learn'}
                    </button>
                    {parameterMappings[`designer:${key}`] && (
                      <button
                        type="button"
                        className="midi-clear"
                        onClick={() => clearParameterMapping(`designer:${key}`)}
                      >
                        CC {parameterMappings[`designer:${key}`].cc}
                      </button>
                    )}
                  </div>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={(draft as any)[key] as number}
                  onChange={e => setDraft(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                />
              </div>
            ))}
          </section>

          <section className="designer-card">
            <h3>Audio reactivo</h3>
            <div className="toggle">
              <input
                type="checkbox"
                checked={draft.audioReactive.density}
                onChange={e => setDraft(prev => ({
                  ...prev,
                  audioReactive: { ...prev.audioReactive, density: e.target.checked },
                }))}
              />
              <span>Partículas reaccionan a amplitud</span>
            </div>
            <div className="toggle">
              <input
                type="checkbox"
                checked={draft.audioReactive.glow}
                onChange={e => setDraft(prev => ({
                  ...prev,
                  audioReactive: { ...prev.audioReactive, glow: e.target.checked },
                }))}
              />
              <span>Glow en beats suaves</span>
            </div>
            <div className="toggle">
              <input
                type="checkbox"
                checked={draft.audioReactive.color}
                onChange={e => setDraft(prev => ({
                  ...prev,
                  audioReactive: { ...prev.audioReactive, color: e.target.checked },
                }))}
              />
              <span>Shifts cromáticos con agudos</span>
            </div>

            <div className="guides">
              <h4>Checklist TouchDesigner-level</h4>
              <ul>
                <li>Capas con parallax + halos volumétricos</li>
                <li>Gradientes holográficos neon (cyan, magenta, fucsia, púrpura)</li>
                <li>Ruido procedural (simplex/Perlin/curl) en deformaciones</li>
                <li>Bloom suave, dispersión de color y depth-of-field sutil</li>
                <li>Partículas con drift, shimmer y trails</li>
              </ul>
            </div>
          </section>
        </div>

        <div className="designer-footer">
          <div className="template-stack">
            <h4>Presets diseñados</h4>
            <div className="template-row">
              {templates.map(t => (
                <div key={t.id} className="template-chip">
                  <strong>{t.name}</strong>
                  <small>{presets.find(p => p.id === t.basePresetId)?.config.name}</small>
                </div>
              ))}
              {templates.length === 0 && <span className="muted">Aún no hay plantillas guardadas.</span>}
            </div>
          </div>
          <div className="footer-actions">
            <button onClick={onClose} className="ghost">Cancelar</button>
            <button onClick={save} className="primary">Guardar preset inmersivo</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImmersivePresetDesigner;
