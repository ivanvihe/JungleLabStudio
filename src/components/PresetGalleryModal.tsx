import React, { useState } from 'react';
import { LAUNCHPAD_PRESETS, LaunchpadPreset } from '../utils/launchpad';
import { LoadedPreset } from '../core/PresetLoader';
import { PresetControls } from './PresetControls';
import { setNestedValue } from '../utils/objectPath';
import { GenLabPresetModal } from './GenLabPresetModal';
import './PresetGalleryModal.css';

interface PresetGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  presets: LoadedPreset[];
  onCustomTextTemplateChange?: (count: number, texts: string[]) => void;
  customTextTemplate?: { count: number; texts: string[] };
  genLabPresets?: { name: string; config: any }[];
  genLabBasePreset?: LoadedPreset | null;
  onGenLabPresetsChange?: (presets: { name: string; config: any }[]) => void;
  onAddPresetToLayer?: (presetId: string, layerId: string) => void;
  onRemovePresetFromLayer?: (presetId: string, layerId: string) => void;
  launchpadPresets?: { id: LaunchpadPreset; label: string }[];
  launchpadPreset?: LaunchpadPreset;
  onLaunchpadPresetChange?: (preset: LaunchpadPreset) => void;
  launchpadRunning?: boolean;
  onToggleLaunchpad?: () => void;
  launchpadText?: string;
  onLaunchpadTextChange?: (text: string) => void;
}

export const PresetGalleryModal: React.FC<PresetGalleryModalProps> = ({
  isOpen,
  onClose,
  presets,
  onCustomTextTemplateChange,
  customTextTemplate = { count: 1, texts: [] },
  genLabPresets = [],
  genLabBasePreset,
  onGenLabPresetsChange,
  onAddPresetToLayer,
  onRemovePresetFromLayer,
  launchpadPresets = LAUNCHPAD_PRESETS,
  launchpadPreset,
  onLaunchpadPresetChange,
  launchpadRunning,
  onToggleLaunchpad,
  launchpadText,
  onLaunchpadTextChange
}) => {
  const [selected, setSelected] = useState<LoadedPreset | null>(null);
  const [activeTab, setActiveTab] = useState<'main' | 'templates' | 'launchpad'>('main');
  const [activeTemplate, setActiveTemplate] = useState<'custom-text' | 'gen-lab' | null>(null);
  const [templateCount, setTemplateCount] = useState(customTextTemplate.count);
  const [templateTexts, setTemplateTexts] = useState<string[]>(() => {
    const arr = [...customTextTemplate.texts];
    while (arr.length < customTextTemplate.count) arr.push(`Text ${arr.length + 1}`);
    if (arr.length > customTextTemplate.count) arr.splice(customTextTemplate.count);
    return arr;
  });
  const [layerAssignments, setLayerAssignments] = useState<Record<string, Set<string>>>(() => ({
    A: new Set(),
    B: new Set(),
    C: new Set()
  }));
  const [editingGenLabIndex, setEditingGenLabIndex] = useState<number | null>(null);
  const [isGenLabModalOpen, setGenLabModalOpen] = useState(false);
  const [selectedLaunchpad, setSelectedLaunchpad] = useState<LaunchpadPreset | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      setTemplateCount(customTextTemplate.count);
      const arr = [...customTextTemplate.texts];
      while (arr.length < customTextTemplate.count) arr.push(`Text ${arr.length + 1}`);
      if (arr.length > customTextTemplate.count) arr.splice(customTextTemplate.count);
      setTemplateTexts(arr);
    }
  }, [isOpen, customTextTemplate]);

  React.useEffect(() => {
    if (isOpen) {
      setSelectedLaunchpad(launchpadPreset || null);
    }
  }, [isOpen, launchpadPreset]);

  const getPresetThumbnail = (preset: LoadedPreset): string => {
    const thumbnails: Record<string, string> = {
      'neural_network': '🧠',
      'abstract-lines': '📈',
      'abstract-lines-pro': '📊',
      'abstract-shapes': '🔷',
      'evolutive-particles': '✨',
      'boom-wave': '💥',
      'plasma-ray': '⚡',
      'shot-text': '📝',
      'text-glitch': '🔤',
      'custom-glitch-text': '📝'
    };
    return thumbnails[preset.id] || thumbnails[preset.id.split('-')[0]] || '🎨';
  };

  const getLaunchpadThumbnail = (id: LaunchpadPreset): string => {
    const icons: Record<LaunchpadPreset, string> = {
      spectrum: '📊',
      pulse: '💓',
      wave: '🌊',
      test: '🧪',
      rainbow: '🌈',
      snake: '🐍',
      canvas: '🖼️',
      'custom-text': '🔤'
    };
    return icons[id] || '🎹';
  };

  const handleSaveGenLabPreset = (preset: { name: string; config: any }) => {
    const list = [...genLabPresets];
    if (editingGenLabIndex !== null) {
      list[editingGenLabIndex] = preset;
    } else {
      list.push(preset);
    }
    onGenLabPresetsChange?.(list);
    setEditingGenLabIndex(null);
  };

  const handleDeleteGenLabPreset = (index: number) => {
    const list = [...genLabPresets];
    list.splice(index, 1);
    onGenLabPresetsChange?.(list);
  };

  const handleDuplicateGenLabPreset = (index: number) => {
    const list = [...genLabPresets];
    const original = list[index];
    const copy = {
      name: `${original.name} Copy`,
      config: JSON.parse(JSON.stringify(original.config))
    };
    list.splice(index + 1, 0, copy);
    onGenLabPresetsChange?.(list);
  };

  const handleTemplateCountChange = (count: number) => {
    const newCount = Math.max(1, Math.min(10, count));
    setTemplateCount(newCount);
    setTemplateTexts(prev => {
      const arr = [...prev];
      while (arr.length < newCount) arr.push(`Text ${arr.length + 1}`);
      if (arr.length > newCount) arr.splice(newCount);
      return arr;
    });
    if (onCustomTextTemplateChange) {
      const arr = [...templateTexts];
      while (arr.length < newCount) arr.push(`Text ${arr.length + 1}`);
      if (arr.length > newCount) arr.splice(newCount);
      onCustomTextTemplateChange(newCount, arr);
    }
  };

  const handleTemplateTextChange = (index: number, value: string) => {
    setTemplateTexts(prev => {
      const arr = [...prev];
      arr[index] = value;
      if (onCustomTextTemplateChange) {
        const clone = [...arr];
        onCustomTextTemplateChange(templateCount, clone);
      }
      return arr;
    });
  };

  // No extra filtering: all presets (including template instances) are shown in main tab

  // Cargar asignaciones actuales desde localStorage al abrir el modal
  React.useEffect(() => {
    if (isOpen) {
      try {
        const stored = localStorage.getItem('layerPresets');
        if (stored) {
          const parsed = JSON.parse(stored);
          setLayerAssignments({
            A: new Set((parsed.A || []).filter((p: string | null) => p)),
            B: new Set((parsed.B || []).filter((p: string | null) => p)),
            C: new Set((parsed.C || []).filter((p: string | null) => p))
          });
        }
      } catch {
        /* ignore */
      }
    }
  }, [isOpen]);

  const toggleLayer = (presetId: string, layerId: string) => {
    setLayerAssignments(prev => {
      const set = new Set(prev[layerId]);
      if (set.has(presetId)) {
        if (onRemovePresetFromLayer) {
          onRemovePresetFromLayer(presetId, layerId);
        }
        set.delete(presetId);
      } else {
        if (onAddPresetToLayer) {
          onAddPresetToLayer(presetId, layerId);
        }
        set.add(presetId);
      }
      return { ...prev, [layerId]: set };
    });
  };

  const handleDefaultControlChange = async (path: string, value: any) => {

    if (!selected) return;

    // Update in-memory default config
    setNestedValue(selected.config.defaultConfig, path, value);

    // Persist to disk using Tauri FS API when available
    try {
      const cfgPath = `${selected.folderPath}/config.json`;
      if (typeof window !== 'undefined' && (window as any).__TAURI__) {
        const { exists, readTextFile, writeFile } = await import(
          /* @vite-ignore */ '@tauri-apps/api/fs'
        );
        if (await exists(cfgPath)) {
          const json = JSON.parse(await readTextFile(cfgPath));
          setNestedValue(json.defaultConfig, path, value);
          await writeFile({ path: cfgPath, contents: JSON.stringify(json, null, 2) });
        }
      }
    } catch (err) {
      console.warn('Could not save default config for', selected.id, err);
    }

    // Force re-render
    setSelected({ ...selected });
  };

  const handleDefaultControlChange = (path: string, value: any) => {
    void persistDefaultConfig(path, value);
  };

  if (!isOpen) return null;

  return (
    <div className="preset-gallery-overlay" onClick={onClose}>
      <div className="preset-gallery-modal" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="preset-gallery-header">
          <h2>🎨 Presets Gallery</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        {/* Tabs */}
        <div className="preset-gallery-tabs">
          <button className={`tab-button ${activeTab === 'main' ? 'active' : ''}`} onClick={() => setActiveTab('main')}>Presets Principales</button>
          <button className={`tab-button ${activeTab === 'templates' ? 'active' : ''}`} onClick={() => setActiveTab('templates')}>Presets Templates</button>
          <button className={`tab-button ${activeTab === 'launchpad' ? 'active' : ''}`} onClick={() => setActiveTab('launchpad')}>LaunchPad Presets</button>
        </div>

        <div className="preset-gallery-content">
          {activeTab === 'main' ? (
            <>
              <div className="preset-gallery-grid preset-gallery-main-grid">
                {presets.map(preset => (
                  <div key={preset.id} className="preset-gallery-item-wrapper">
                    <div
                      className="preset-gallery-item preset-cell"
                      onClick={() => setSelected(preset)}
                    >
                      {preset.config.note !== undefined && (
                        <div className="preset-note-badge">{preset.config.note}</div>
                      )}
                      <div className="preset-thumbnail">{getPresetThumbnail(preset)}</div>
                      <div className="preset-info">
                        <div className="preset-name">{preset.config.name}</div>
                        <div className="preset-details">
                          <span className="preset-category">{preset.config.category}</span>
                        </div>
                      </div>
                    </div>

                    {/* Botones de capas */}
                    <div className="layer-button-group">
                      {['A', 'B', 'C'].map(layer => (
                        <button
                          key={layer}
                          className={`layer-button ${layerAssignments[layer].has(preset.id) ? 'active' : ''}`}
                          onClick={e => {
                            e.stopPropagation();
                            toggleLayer(preset.id, layer);
                          }}
                        >
                          {layer}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {selected ? (
                <div className="gallery-controls-panel">
                  <div className="controls-header">
                    <h3>{selected.config.name}</h3>
                    <span className="preset-category-badge">{selected.config.category}</span>
                  </div>

                  {/* Controles por defecto del preset */}
                  <div className="default-controls">
                    <h4>Valores por defecto:</h4>
                    <PresetControls
                      preset={selected}
                      config={selected.config.defaultConfig || {}}
                      onChange={handleDefaultControlChange}
                    />
                  </div>
                </div>
              ) : (
                <div className="preset-gallery-placeholder">
                  <div className="placeholder-content">
                    <div className="placeholder-icon">🎯</div>
                    <h3>Selecciona un preset</h3>
                    <p>Haz click en un preset para ver y editar sus valores por defecto</p>
                    <div className="placeholder-instructions">
                      <div>• <strong>Click:</strong> Ver controles y configuración</div>
                      <div>• <strong>A/B/C:</strong> Añadir o quitar de una layer</div>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : activeTab === 'templates' ? (
            <div className="templates-layout">
              <div className="template-selector">
                <div className="preset-gallery-grid template-selector-grid">
                  <div className="preset-gallery-item-wrapper">
                    <div
                      className="preset-gallery-item preset-cell"
                      onClick={() => setActiveTemplate('custom-text')}
                    >
                      <div className="preset-thumbnail">📝</div>
                      <div className="preset-info">
                        <div className="preset-name">Custom Text</div>
                        <div className="preset-details">
                          <span className="preset-category">Template</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="preset-gallery-item-wrapper">
                    <div
                      className="preset-gallery-item preset-cell"
                      onClick={() => setActiveTemplate('gen-lab')}
                    >
                      <div className="preset-thumbnail">🔬</div>
                      <div className="preset-info">
                        <div className="preset-name">Gen Lab</div>
                        <div className="preset-details">
                          <span className="preset-category">Template</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="template-controls-panel">
                {!activeTemplate && (
                  <div className="preset-gallery-placeholder">
                    <div className="placeholder-content">
                      <div className="placeholder-icon">📁</div>
                      <h3>Select a template</h3>
                      <p>Choose a template to configure it</p>
                    </div>
                  </div>
                )}
                {activeTemplate === 'custom-text' && (
                  <div className="custom-text-config">
                    <label>Cantidad:</label>
                    <div className="count-controls">
                      <button onClick={() => handleTemplateCountChange(templateCount - 1)} disabled={templateCount <= 1}>-</button>
                      <span className="count-display">{templateCount}</span>
                      <button onClick={() => handleTemplateCountChange(templateCount + 1)} disabled={templateCount >= 10}>+</button>
                    </div>
                    <div className="custom-text-inputs">
                      {templateTexts.map((txt, idx) => (
                        <input
                          key={idx}
                          type="text"
                          value={txt}
                          onChange={e => handleTemplateTextChange(idx, e.target.value)}
                        />
                      ))}
                    </div>
                  </div>
                )}
                {activeTemplate === 'gen-lab' && (
                  <div className="genlab-config">
                    <button className="genlab-add-button" onClick={() => { setEditingGenLabIndex(null); setGenLabModalOpen(true); }}>Add Preset</button>
                    <ul className="genlab-list">
                      {genLabPresets.map((p, idx) => (
                        <li key={idx}>
                          <span>{p.name}</span>
                          <div>
                            <button onClick={() => { setEditingGenLabIndex(idx); setGenLabModalOpen(true); }}>Edit</button>
                            <button onClick={() => handleDuplicateGenLabPreset(idx)}>Duplicate</button>
                            <button onClick={() => handleDeleteGenLabPreset(idx)}>Delete</button>
                          </div>
                        </li>
                      ))}
                    </ul>
                    {genLabBasePreset && (
                      <GenLabPresetModal
                        isOpen={isGenLabModalOpen}
                        onClose={() => { setGenLabModalOpen(false); setEditingGenLabIndex(null); }}
                        basePreset={genLabBasePreset}
                        initial={editingGenLabIndex !== null ? genLabPresets[editingGenLabIndex] : undefined}
                        onSave={handleSaveGenLabPreset}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="launchpad-layout">
              <div className="launchpad-selector">
                <div className="preset-gallery-grid launchpad-selector-grid">
                  {launchpadPresets.map(lp => (
                    <div key={lp.id} className="preset-gallery-item-wrapper">
                      <div
                        className="preset-gallery-item preset-cell"
                        onClick={() => {
                          setSelectedLaunchpad(lp.id);
                          onLaunchpadPresetChange?.(lp.id);
                        }}
                      >
                        <div className="preset-thumbnail">{getLaunchpadThumbnail(lp.id)}</div>
                        <div className="preset-info">
                          <div className="preset-name">{lp.label}</div>
                          <div className="preset-details">
                            <span className="preset-category">LaunchPad</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="launchpad-controls-panel">
                {!selectedLaunchpad && (
                  <div className="preset-gallery-placeholder">
                    <div className="placeholder-content">
                      <div className="placeholder-icon">🎹</div>
                      <h3>Select a launchpad preset</h3>
                      <p>Click a preset to configure it</p>
                    </div>
                  </div>
                )}
                {selectedLaunchpad && (
                  <>
                    <div className="controls-header">
                      <h3>{launchpadPresets.find(p => p.id === selectedLaunchpad)?.label}</h3>
                      <span className="preset-category-badge">LaunchPad</span>
                    </div>
                    {selectedLaunchpad === 'custom-text' && (
                      <div className="default-controls">
                        <h4>Text:</h4>
                        <input
                          type="text"
                          value={launchpadText || ''}
                          onChange={e => onLaunchpadTextChange?.(e.target.value)}
                        />
                      </div>
                    )}
                    <button
                      className={`launchpad-button ${launchpadRunning ? 'running' : ''}`}
                      onClick={onToggleLaunchpad}
                    >
                      {launchpadRunning ? 'Stop Launchpad' : 'Go Launchpad'}
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};