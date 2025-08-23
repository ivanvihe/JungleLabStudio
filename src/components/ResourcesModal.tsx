import React, { useState, useEffect, useRef } from 'react';
import { LAUNCHPAD_PRESETS, LaunchpadPreset } from '../utils/launchpad';
import { LoadedPreset } from '../core/PresetLoader';
import { PresetControls } from './PresetControls';
import { setNestedValue } from '../utils/objectPath';
import { GenLabPresetModal } from './GenLabPresetModal';
import './ResourcesModal.css';

interface ResourcesModalProps {
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

type NodeKind =
  | 'folder'
  | 'preset'
  | 'custom-text'
  | 'genlab-folder'
  | 'genlab-item'
  | 'launchpad';

interface TreeNode {
  id: string;
  label: string;
  kind: NodeKind;
  children?: TreeNode[];
  preset?: LoadedPreset;
  launchpadId?: LaunchpadPreset;
  genLabIndex?: number;
}

export const ResourcesModal: React.FC<ResourcesModalProps> = ({
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
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set([
    'visual',
    'visual-main',
    'visual-custom',
    'templates',
    'template-genlab',
    'launchpad'
  ]));
  const [sidebarWidth, setSidebarWidth] = useState(220);
  const [isResizing, setIsResizing] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    if (isOpen) {
      setTemplateCount(customTextTemplate.count);
      const arr = [...customTextTemplate.texts];
      while (arr.length < customTextTemplate.count) arr.push(`Text ${arr.length + 1}`);
      if (arr.length > customTextTemplate.count) arr.splice(customTextTemplate.count);
      setTemplateTexts(arr);
    }
  }, [isOpen, customTextTemplate]);

  useEffect(() => {
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

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const rect = modalRef.current?.getBoundingClientRect();
      if (rect) {
        const width = Math.min(rect.width - 100, Math.max(150, e.clientX - rect.left));
        setSidebarWidth(width);
      }
    };
    const handleMouseUp = () => setIsResizing(false);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

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
    if (selectedNode?.kind === 'genlab-item' && selectedNode.genLabIndex === index) {
      setSelectedNode(null);
    }
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

  const toggleLayer = (presetId: string, layerId: string) => {
    setLayerAssignments(prev => {
      const set = new Set(prev[layerId]);
      if (set.has(presetId)) {
        onRemovePresetFromLayer?.(presetId, layerId);
        set.delete(presetId);
      } else {
        onAddPresetToLayer?.(presetId, layerId);
        set.add(presetId);
      }
      return { ...prev, [layerId]: set };
    });
  };

  const handleDefaultControlChange = async (path: string, value: any) => {
    if (!selectedNode || selectedNode.kind !== 'preset') return;
    const preset = selectedNode.preset!;
    setNestedValue(preset.config.defaultConfig, path, value);
    try {
      const cfgPath = `${preset.folderPath}/config.json`;
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
      console.warn('Could not save default config for', preset.id, err);
    }
    setSelectedNode({ ...selectedNode });
  };

  if (!isOpen) return null;

  const mainPresets = presets.filter(
    p => !p.id.startsWith('custom-glitch-text') && !p.id.startsWith('gen-lab-')
  );
  const customPresets = presets.filter(
    p => p.id.startsWith('custom-glitch-text') || p.id.startsWith('gen-lab-')
  );

  const tree: TreeNode[] = [
    {
      id: 'visual',
      label: 'Visual presets',
      kind: 'folder',
      children: [
        {
          id: 'visual-main',
          label: 'Main presets',
          kind: 'folder',
          children: mainPresets.map(p => ({
            id: p.id,
            label: p.config.name,
            kind: 'preset',
            preset: p
          }))
        },
        {
          id: 'visual-custom',
          label: 'Custom presets',
          kind: 'folder',
          children: customPresets.map(p => ({
            id: p.id,
            label: p.config.name,
            kind: 'preset',
            preset: p
          }))
        }
      ]
    },
    {
      id: 'templates',
      label: 'Templates',
      kind: 'folder',
      children: [
        { id: 'template-custom-text', label: 'Custom text', kind: 'custom-text' },
        {
          id: 'template-genlab',
          label: 'Gen Lab',
          kind: 'genlab-folder',
          children: genLabPresets.map((p, idx) => ({
            id: `genlab-${idx}`,
            label: p.name,
            kind: 'genlab-item',
            genLabIndex: idx
          }))
        }
      ]
    },
    {
      id: 'launchpad',
      label: 'LaunchPad',
      kind: 'folder',
      children: launchpadPresets.map(lp => ({
        id: `lp-${lp.id}`,
        label: lp.label,
        kind: 'launchpad',
        launchpadId: lp.id
      }))
    }
  ];

  const renderNode = (node: TreeNode, depth = 0) => {
    const isFolder = node.kind === 'folder' || node.kind === 'genlab-folder';
    const expandedNode = expanded.has(node.id);
    return (
      <div key={node.id}>
        <div
          className={`tree-node ${selectedNode?.id === node.id ? 'selected' : ''}`}
          style={{ paddingLeft: depth * 16 }}
        >
          {isFolder && (
            <span className="expander" onClick={() => toggleExpand(node.id)}>
              {expandedNode ? '▼' : '▶'}
            </span>
          )}
          <span
            className="node-label"
            onClick={() => {
              setSelectedNode(node);
              if (node.kind === 'launchpad') {
                onLaunchpadPresetChange?.(node.launchpadId!);
              }
            }}
          >
            {isFolder ? '📁' : node.kind === 'launchpad' ? getLaunchpadThumbnail(node.launchpadId!) : node.kind === 'preset' ? getPresetThumbnail(node.preset!) : '📄'}{' '}
            {node.label}
          </span>
        </div>
        {isFolder && expandedNode && node.children && (
          <div className="tree-children">
            {node.children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  const renderDetails = () => {
    if (!selectedNode) {
      return (
        <div className="preset-gallery-placeholder">
          <div className="placeholder-content">
            <div className="placeholder-icon">🎯</div>
            <h3>Select a resource</h3>
          </div>
        </div>
      );
    }

    switch (selectedNode.kind) {
      case 'preset': {
        const preset = selectedNode.preset!;
        return (
          <div className="gallery-controls-panel">
            <div className="controls-header">
              <h3>{preset.config.name}</h3>
              <span className="preset-category-badge">{preset.config.category}</span>
            </div>
            <div className="layer-button-group">
              {['A', 'B', 'C'].map(layer => (
                <button
                  key={layer}
                  className={`layer-button ${layerAssignments[layer].has(preset.id) ? 'active' : ''}`}
                  onClick={() => toggleLayer(preset.id, layer)}
                >
                  {layer}
                </button>
              ))}
            </div>
            <div className="default-controls">
              <h4>Default values:</h4>
              <PresetControls
                preset={preset}
                config={preset.config.defaultConfig || {}}
                onChange={handleDefaultControlChange}
              />
            </div>
          </div>
        );
      }
      case 'custom-text': {
        return (
          <div className="template-controls-panel">
            <div className="custom-text-config">
              <label>Count:</label>
              <div className="count-controls">
                <button onClick={() => handleTemplateCountChange(templateCount - 1)} disabled={templateCount <= 1}>
                  -
                </button>
                <span className="count-display">{templateCount}</span>
                <button onClick={() => handleTemplateCountChange(templateCount + 1)} disabled={templateCount >= 10}>
                  +
                </button>
              </div>
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
        );
      }
      case 'genlab-folder': {
        return (
          <div className="genlab-config">
            <button
              className="genlab-add-button"
              onClick={() => {
                setEditingGenLabIndex(null);
                setGenLabModalOpen(true);
              }}
            >
              Add Preset
            </button>
            <ul className="genlab-list">
              {genLabPresets.map((p, idx) => (
                <li
                  key={idx}
                  onClick={() =>
                    setSelectedNode({
                      id: `genlab-${idx}`,
                      label: p.name,
                      kind: 'genlab-item',
                      genLabIndex: idx
                    })
                  }
                >
                  <span>{p.name}</span>
                  <div>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        setEditingGenLabIndex(idx);
                        setGenLabModalOpen(true);
                      }}
                    >
                      Edit
                    </button>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        handleDuplicateGenLabPreset(idx);
                      }}
                    >
                      Duplicate
                    </button>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        handleDeleteGenLabPreset(idx);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            {genLabBasePreset && (
              <GenLabPresetModal
                isOpen={isGenLabModalOpen}
                onClose={() => {
                  setGenLabModalOpen(false);
                  setEditingGenLabIndex(null);
                }}
                basePreset={genLabBasePreset}
                initial={
                  editingGenLabIndex !== null ? genLabPresets[editingGenLabIndex] : undefined
                }
                onSave={handleSaveGenLabPreset}
              />
            )}
          </div>
        );
      }
      case 'genlab-item': {
        const idx = selectedNode.genLabIndex!;
        const item = genLabPresets[idx];
        return (
          <div className="genlab-config">
            <h3>{item.name}</h3>
            <div>
              <button
                onClick={() => {
                  setEditingGenLabIndex(idx);
                  setGenLabModalOpen(true);
                }}
              >
                Edit
              </button>
              <button onClick={() => handleDuplicateGenLabPreset(idx)}>Duplicate</button>
              <button onClick={() => handleDeleteGenLabPreset(idx)}>Delete</button>
            </div>
            {genLabBasePreset && (
              <GenLabPresetModal
                isOpen={isGenLabModalOpen}
                onClose={() => {
                  setGenLabModalOpen(false);
                  setEditingGenLabIndex(null);
                }}
                basePreset={genLabBasePreset}
                initial={
                  editingGenLabIndex !== null ? genLabPresets[editingGenLabIndex] : undefined
                }
                onSave={handleSaveGenLabPreset}
              />
            )}
          </div>
        );
      }
      case 'launchpad': {
        const lpId = selectedNode.launchpadId!;
        return (
          <div className="launchpad-controls-panel">
            <div className="controls-header">
              <h3>{launchpadPresets.find(p => p.id === lpId)?.label}</h3>
              <span className="preset-category-badge">LaunchPad</span>
            </div>
            {lpId === 'custom-text' && (
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
          </div>
        );
      }
      default:
        return null;
    }
  };

  return (
    <div className="preset-gallery-overlay" onClick={onClose}>
      <div
        className="preset-gallery-modal"
        onClick={e => e.stopPropagation()}
        ref={modalRef}
        style={{ ['--sidebar-width' as any]: `${sidebarWidth}px` }}
      >
        <div className="preset-gallery-header">
          <h2>📁 Resources</h2>
          <button className="close-button" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="resources-layout">
          <div className="resources-tree">
            {tree.map(node => renderNode(node))}
          </div>
          <div
            className="resources-resizer"
            onMouseDown={() => setIsResizing(true)}
          ></div>
          <div className="resources-details">{renderDetails()}</div>
        </div>
      </div>
    </div>
  );
};

