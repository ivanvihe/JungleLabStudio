import React, { useMemo, useState } from 'react';
import './GlobalSettingsModal.css';

import { AudioSettings } from './settings/AudioSettings';
import { MidiSettings } from './settings/MidiSettings';
import { LaunchpadSettings } from './settings/LaunchpadSettings';
import { VideoSettings } from './settings/VideoSettings';
import { FullscreenSettings } from './settings/FullscreenSettings';
import { VisualSettings } from './settings/VisualSettings';
import { SystemSettings } from './settings/SystemSettings';
import { AutomationSettings } from './settings/AutomationSettings';
import { ProjectSettings } from './settings/ProjectSettings';
import { VideoProviderSettings as VideoProviderSettingsSection } from './settings/VideoProviderSettings';
import { VideoProviderId } from '../utils/videoProviders';
import { CronJob } from '../types/automation';
import { ProjectConfig, ProjectValidationResult } from '../types/projects';
import { CommandRunResult } from '../utils/commandRunner';

interface DeviceOption {
  id: string;
  label: string;
}

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  isPrimary: boolean;
  scaleFactor: number;
}

interface MidiClockSettings {
  resolution: number;
  delay: number;
  quantization: number;
  jumpMode: boolean;
  stability: number;
  type: 'midi' | 'internal' | 'off';
}

interface GlobalSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  audioDevices: DeviceOption[];
  midiDevices: DeviceOption[];
  launchpadDevices: DeviceOption[];
  selectedAudioId: string | null;
  selectedMidiId: string | null;
  selectedLaunchpadId: string | null;
  onSelectAudio: (id: string) => void;
  onSelectMidi: (id: string) => void;
  onSelectLaunchpad: (id: string | null) => void;
  audioGain: number;
  onAudioGainChange: (value: number) => void;
  midiClockSettings: MidiClockSettings;
  onUpdateClockSettings: (updates: Partial<MidiClockSettings>) => void;
  internalBpm: number;
  onSetInternalBpm: (bpm: number) => void;
  clockStable: boolean;
  currentMeasure: number;
  currentBeat: number;
  layerChannels: Record<string, number>;
  onLayerChannelChange: (layerId: string, channel: number) => void;
  effectMidiNotes: Record<string, number>;
  onEffectMidiNoteChange: (effect: string, note: number) => void;
  launchpadChannel: number;
  onLaunchpadChannelChange: (value: number) => void;
  launchpadNote: number;
  onLaunchpadNoteChange: (value: number) => void;
  launchpadSmoothness: number;
  onLaunchpadSmoothnessChange: (value: number) => void;
  monitors: MonitorInfo[];
  monitorRoles: Record<string, 'main' | 'secondary' | 'none'>;
  onMonitorRoleChange: (id: string, role: 'main' | 'secondary' | 'none') => void;
  startMonitor: string | null;
  onStartMonitorChange: (id: string | null) => void;
  glitchTextPads: number;
  onGlitchPadChange: (value: number) => void;
  hideUiHotkey: string;
  onHideUiHotkeyChange: (value: string) => void;
  fullscreenHotkey: string;
  onFullscreenHotkeyChange: (value: string) => void;
  exitFullscreenHotkey: string;
  onExitFullscreenHotkeyChange: (value: string) => void;
  fullscreenByDefault: boolean;
  onFullscreenByDefaultChange: (value: boolean) => void;
  startMaximized: boolean;
  onStartMaximizedChange: (value: boolean) => void;
  canvasBrightness: number;
  onCanvasBrightnessChange: (value: number) => void;
  canvasVibrance: number;
  onCanvasVibranceChange: (value: number) => void;
  canvasBackground: string;
  onCanvasBackgroundChange: (value: string) => void;
  visualsPath: string;
  onVisualsPathChange: (value: string) => void;
  videoProvider: VideoProviderId;
  videoApiKey: string;
  videoQuery: string;
  videoRefreshMinutes: number;
  onVideoProviderChange: (provider: VideoProviderId) => void;
  onVideoApiKeyChange: (value: string) => void;
  onVideoQueryChange: (value: string) => void;
  onVideoRefreshMinutesChange: (value: number) => void;
  onVideoCacheClear: () => void;
  cronJobs: CronJob[];
  onCronJobSave: (job: CronJob) => void;
  onCronJobDelete: (jobId: string) => void;
  onCronJobToggle: (jobId: string, enabled: boolean) => void;
  onCronJobRun: (jobId: string) => void;
  projects: ProjectConfig[];
  onProjectSave: (project: ProjectConfig) => void;
  onProjectDelete: (projectId: string) => void;
  onProjectSync: (projectId: string) => Promise<CommandRunResult>;
  onProjectClone: (project: ProjectConfig) => Promise<CommandRunResult>;
  onProjectValidate: (project: ProjectConfig) => Promise<ProjectValidationResult>;
}

const GlobalSettingsModal: React.FC<GlobalSettingsModalProps> = ({
  isOpen,
  onClose,
  audioDevices,
  midiDevices,
  launchpadDevices,
  selectedAudioId,
  selectedMidiId,
  selectedLaunchpadId,
  onSelectAudio,
  onSelectMidi,
  onSelectLaunchpad,
  audioGain,
  onAudioGainChange,
  midiClockSettings,
  onUpdateClockSettings,
  internalBpm,
  onSetInternalBpm,
  clockStable,
  currentMeasure,
  currentBeat,
  layerChannels,
  onLayerChannelChange,
  effectMidiNotes,
  onEffectMidiNoteChange,
  launchpadChannel,
  onLaunchpadChannelChange,
  launchpadNote,
  onLaunchpadNoteChange,
  launchpadSmoothness,
  onLaunchpadSmoothnessChange,
  monitors,
  monitorRoles,
  onMonitorRoleChange,
  startMonitor,
  onStartMonitorChange,
  glitchTextPads,
  onGlitchPadChange,
  hideUiHotkey,
  onHideUiHotkeyChange,
  fullscreenHotkey,
  onFullscreenHotkeyChange,
  exitFullscreenHotkey,
  onExitFullscreenHotkeyChange,
  fullscreenByDefault,
  onFullscreenByDefaultChange,
  startMaximized,
  onStartMaximizedChange,
  canvasBrightness,
  onCanvasBrightnessChange,
  canvasVibrance,
  onCanvasVibranceChange,
  canvasBackground,
  onCanvasBackgroundChange,
  visualsPath,
  onVisualsPathChange,
  videoProvider,
  videoApiKey,
  videoQuery,
  videoRefreshMinutes,
  onVideoProviderChange,
  onVideoApiKeyChange,
  onVideoQueryChange,
  onVideoRefreshMinutesChange,
  onVideoCacheClear,
  cronJobs,
  onCronJobSave,
  onCronJobDelete,
  onCronJobToggle,
  onCronJobRun,
  projects,
  onProjectSave,
  onProjectDelete,
  onProjectSync,
  onProjectClone,
  onProjectValidate,
}) => {
  const [activeTab, setActiveTab] = useState('audio');

  type PreferenceNode = {
    id: string;
    label: string;
    icon: string;
    children?: PreferenceNode[];
    tabId?: string;
  };

  const preferenceTree = useMemo<PreferenceNode[]>(
    () => [
      {
        id: 'audio-group',
        label: 'Audio & MIDI',
        icon: '🎵',
        children: [
          { id: 'audio', label: 'Audio engine', icon: '🔊', tabId: 'audio' },
          {
            id: 'hardware',
            label: 'MIDI & Launchpad',
            icon: '🎛️',
            tabId: 'hardware',
          },
        ],
      },
      {
        id: 'visual-group',
        label: 'Visual workflow',
        icon: '🎨',
        children: [
          { id: 'video', label: 'Performance', icon: '🎮', tabId: 'video' },
          {
            id: 'videos',
            label: 'Video providers',
            icon: '🎞️',
            tabId: 'videos',
          },
          {
            id: 'fullscreen',
            label: 'Monitors',
            icon: '🖥️',
            tabId: 'fullscreen',
          },
          { id: 'visual', label: 'Visual tweaks', icon: '🌈', tabId: 'visual' },
        ],
      },
      {
        id: 'system-group',
        label: 'System',
        icon: '🛠️',
        children: [
          {
            id: 'system',
            label: 'System & maintenance',
            icon: '🔧',
            tabId: 'system',
          },
        ],
      },
      {
        id: 'automation-group',
        label: 'Automation',
        icon: '⏱️',
        children: [
          {
            id: 'automation',
            label: 'Cron jobs',
            icon: '🕒',
            tabId: 'automation',
          },
        ],
      },
      {
        id: 'projects-group',
        label: 'Projects',
        icon: '📂',
        children: [
          {
            id: 'projects',
            label: 'GitHub projects',
            icon: '🐙',
            tabId: 'projects',
          },
        ],
      },
    ],
    []
  );

  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(
    () => new Set(preferenceTree.map((node) => node.id))
  );

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const renderNode = (node: PreferenceNode, depth = 0): React.ReactNode => {
    const isLeaf = !node.children || node.children.length === 0;
    const isExpanded = expandedNodes.has(node.id);
    const targetTab = node.tabId || node.id;
    const isActive = isLeaf && activeTab === targetTab;

    return (
      <li
        key={node.id}
        className={`preferences-node ${isLeaf ? 'leaf' : 'branch'}`}
      >
        <button
          type="button"
          className={`preferences-node__label ${isLeaf && isActive ? 'active' : ''}`}
          style={{ paddingLeft: `${12 + depth * 12}px` }}
          onClick={() => {
            if (isLeaf) {
              setActiveTab(targetTab);
            } else {
              toggleNode(node.id);
            }
          }}
        >
          {!isLeaf && (
            <span className="preferences-expander">{isExpanded ? '▼' : '▶'}</span>
          )}
          <span className="preferences-node__icon">{node.icon}</span>
          <span>{node.label}</span>
        </button>
        {!isLeaf && isExpanded && node.children && (
          <ul className="preferences-children">
            {node.children.map((child) => renderNode(child, depth + 1))}
          </ul>
        )}
      </li>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal-content">
        <div className="settings-header">
          <h2>⚙️ Global Settings</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="settings-main">
          <div className="settings-sidebar">
            <ul className="preferences-tree">
              {preferenceTree.map((node) => renderNode(node))}
            </ul>
          </div>

          <div className="settings-content">
            {activeTab === 'audio' && (
              <AudioSettings
                audioDevices={audioDevices}
                selectedAudioId={selectedAudioId}
                onSelectAudio={onSelectAudio}
                audioGain={audioGain}
                onAudioGainChange={onAudioGainChange}
              />
            )}

            {activeTab === 'hardware' && (
              <div className="settings-section">
                <MidiSettings
                  midiDevices={midiDevices}
                  selectedMidiId={selectedMidiId}
                  onSelectMidi={onSelectMidi}
                  midiClockSettings={midiClockSettings}
                  onUpdateClockSettings={onUpdateClockSettings}
                  internalBpm={internalBpm}
                  onSetInternalBpm={onSetInternalBpm}
                  clockStable={clockStable}
                  currentMeasure={currentMeasure}
                  currentBeat={currentBeat}
                  layerChannels={layerChannels}
                  onLayerChannelChange={onLayerChannelChange}
                  effectMidiNotes={effectMidiNotes}
                  onEffectMidiNoteChange={onEffectMidiNoteChange}
                />
                <LaunchpadSettings
                  launchpadDevices={launchpadDevices}
                  selectedLaunchpadId={selectedLaunchpadId}
                  onSelectLaunchpad={onSelectLaunchpad}
                  launchpadChannel={launchpadChannel}
                  onLaunchpadChannelChange={onLaunchpadChannelChange}
                  launchpadNote={launchpadNote}
                  onLaunchpadNoteChange={onLaunchpadNoteChange}
                  launchpadSmoothness={launchpadSmoothness}
                  onLaunchpadSmoothnessChange={onLaunchpadSmoothnessChange}
                />
              </div>
            )}

            {activeTab === 'video' && <VideoSettings />}

            {activeTab === 'videos' && (
              <VideoProviderSettingsSection
                provider={videoProvider}
                apiKey={videoApiKey}
                refreshMinutes={videoRefreshMinutes}
                query={videoQuery}
                onProviderChange={onVideoProviderChange}
                onApiKeyChange={onVideoApiKeyChange}
                onRefreshMinutesChange={onVideoRefreshMinutesChange}
                onQueryChange={onVideoQueryChange}
                onClearCache={onVideoCacheClear}
              />
            )}

            {activeTab === 'fullscreen' && (
              <FullscreenSettings
                monitors={monitors}
                monitorRoles={monitorRoles}
                onMonitorRoleChange={onMonitorRoleChange}
              />
            )}

            {activeTab === 'visual' && (
              <VisualSettings
                hideUiHotkey={hideUiHotkey}
                onHideUiHotkeyChange={onHideUiHotkeyChange}
                fullscreenHotkey={fullscreenHotkey}
                onFullscreenHotkeyChange={onFullscreenHotkeyChange}
                exitFullscreenHotkey={exitFullscreenHotkey}
                onExitFullscreenHotkeyChange={onExitFullscreenHotkeyChange}
                fullscreenByDefault={fullscreenByDefault}
                onFullscreenByDefaultChange={onFullscreenByDefaultChange}
                canvasBrightness={canvasBrightness}
                onCanvasBrightnessChange={onCanvasBrightnessChange}
                canvasVibrance={canvasVibrance}
                onCanvasVibranceChange={onCanvasVibranceChange}
                canvasBackground={canvasBackground}
                onCanvasBackgroundChange={onCanvasBackgroundChange}
                glitchTextPads={glitchTextPads}
                onGlitchPadChange={onGlitchPadChange}
              />
            )}


            {activeTab === 'system' && (
              <SystemSettings
                startMaximized={startMaximized}
                onStartMaximizedChange={onStartMaximizedChange}
                monitors={monitors}
                startMonitor={startMonitor}
                onStartMonitorChange={onStartMonitorChange}
                visualsPath={visualsPath}
                onVisualsPathChange={onVisualsPathChange}
              />
            )}

            {activeTab === 'automation' && (
              <AutomationSettings
                cronJobs={cronJobs}
                onSaveJob={onCronJobSave}
                onDeleteJob={onCronJobDelete}
                onToggleJob={onCronJobToggle}
                onRunJob={onCronJobRun}
              />
            )}

            {activeTab === 'projects' && (
              <ProjectSettings
                projects={projects}
                onSaveProject={onProjectSave}
                onDeleteProject={onProjectDelete}
                onSyncProject={onProjectSync}
                onCloneProject={onProjectClone}
                onValidateProject={onProjectValidate}
              />
            )}
          </div>
        </div>

        <div className="settings-footer">
          <div className="settings-info">
            <span>💡 Changes are applied automatically</span>
          </div>
          <button className="primary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default GlobalSettingsModal;

