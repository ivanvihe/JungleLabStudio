import React, { useEffect, useMemo, useState } from 'react';
import {
  ProjectConfig,
  ProjectValidationResult
} from '../../types/projects';
import { validateCronExpression, getNextRun } from '../../utils/cron';
import { CommandRunResult } from '../../utils/commandRunner';
import './ProjectSettings.css';

interface ProjectSettingsProps {
  projects: ProjectConfig[];
  onSaveProject: (project: ProjectConfig) => void;
  onDeleteProject: (projectId: string) => void;
  onSyncProject: (projectId: string) => Promise<CommandRunResult>;
  onCloneProject: (project: ProjectConfig) => Promise<CommandRunResult>;
  onValidateProject: (project: ProjectConfig) => Promise<ProjectValidationResult>;
}

type ProjectFormState = ProjectConfig;

const emptyProject: ProjectFormState = {
  id: '',
  name: '',
  localPath: '',
  repoUrl: '',
  defaultBranch: 'main',
  personalAccessToken: '',
  autoSyncCron: '',
  description: ''
};

function createProjectId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `project-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function formatSyncStatus(project?: ProjectConfig): string {
  if (!project?.lastSyncStatus || !project.lastSyncAt) {
    return 'Never synced';
  }
  const date = project.lastSyncAt
    ? new Date(project.lastSyncAt).toLocaleString()
    : 'unknown time';
  const message = project.lastSyncMessage ? ` – ${project.lastSyncMessage}` : '';
  return `${project.lastSyncStatus.toUpperCase()} (${date})${message}`;
}

export const ProjectSettings: React.FC<ProjectSettingsProps> = ({
  projects,
  onSaveProject,
  onDeleteProject,
  onSyncProject,
  onCloneProject,
  onValidateProject
}) => {
  const sortedProjects = useMemo(
    () => [...projects].sort((a, b) => a.name.localeCompare(b.name)),
    [projects]
  );

  const [selectedId, setSelectedId] = useState<string | null>(
    sortedProjects[0]?.id ?? null
  );
  const [formState, setFormState] = useState<ProjectFormState>(emptyProject);
  const [cronError, setCronError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    if (!selectedId) {
      setFormState(emptyProject);
      setCronError(null);
      return;
    }
    const project = projects.find((item) => item.id === selectedId);
    if (project) {
      setFormState({
        ...project,
        personalAccessToken: project.personalAccessToken || ''
      });
      setCronError(null);
    }
  }, [selectedId, projects]);

  useEffect(() => {
    if (projects.length === 0) {
      setSelectedId(null);
    }
  }, [projects.length]);

  const handleChange = <K extends keyof ProjectFormState>(
    key: K,
    value: ProjectFormState[K]
  ) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
    if (key === 'autoSyncCron') {
      setCronError(null);
    }
  };

  const ensureProjectId = () => {
    const id = formState.id || createProjectId();
    if (!formState.id) {
      setFormState((prev) => ({ ...prev, id }));
    }
    return id;
  };

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();
    if (!formState.name.trim()) {
      setFeedback('Please provide a project name');
      return;
    }
    if (!formState.repoUrl.trim()) {
      setFeedback('Repository URL is required');
      return;
    }
    if (!formState.localPath.trim()) {
      setFeedback('Local path is required');
      return;
    }

    if (formState.autoSyncCron) {
      const error = validateCronExpression(formState.autoSyncCron);
      if (error) {
        setCronError(error);
        return;
      }
    }

    const id = ensureProjectId();
    const payload: ProjectConfig = {
      ...formState,
      id,
      name: formState.name.trim(),
      repoUrl: formState.repoUrl.trim(),
      localPath: formState.localPath.trim(),
      defaultBranch: formState.defaultBranch.trim() || 'main',
      personalAccessToken: formState.personalAccessToken?.trim() || undefined,
      autoSyncCron: formState.autoSyncCron?.trim() || undefined,
      description: formState.description?.trim() || undefined
    };

    onSaveProject(payload);
    setSelectedId(id);
    setFeedback('Project saved');
    window.setTimeout(() => setFeedback(null), 3000);
  };

  const handleDeleteProject = (projectId: string) => {
    if (!window.confirm('Remove this project configuration?')) {
      return;
    }
    onDeleteProject(projectId);
    if (selectedId === projectId) {
      setSelectedId(null);
    }
  };

  const handleValidate = async () => {
    setIsBusy(true);
    try {
      const result = await onValidateProject(formState);
      setFeedback(result.message);
      if (result.success && result.defaultBranch) {
        setFormState((prev) => ({ ...prev, defaultBranch: result.defaultBranch! }));
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setFeedback(`Validation error: ${message}`);
    } finally {
      setIsBusy(false);
    }
  };

  const handleClone = async () => {
    setIsBusy(true);
    try {
      const result = await onCloneProject({
        ...formState,
        id: ensureProjectId()
      });
      setFeedback(result.success ? result.stdout || 'Clone complete' : result.errorMessage || result.stderr);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setFeedback(`Clone error: ${message}`);
    } finally {
      setIsBusy(false);
    }
  };

  const handleSync = async (id?: string) => {
    const projectId = id ?? formState.id;
    if (!projectId) {
      return;
    }
    setIsBusy(true);
    try {
      const result = await onSyncProject(projectId);
      setFeedback(result.success ? result.stdout || 'Sync complete' : result.errorMessage || result.stderr);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setFeedback(`Sync error: ${message}`);
    } finally {
      setIsBusy(false);
    }
  };

  const nextSync = formState.autoSyncCron
    ? getNextRun(formState.autoSyncCron)
    : null;

  return (
    <div className="project-settings">
      <h3>🐙 GitHub Projects</h3>
      <p className="setting-description">
        Centralize the configuration of local projects linked to GitHub repositories.
        You can validate connectivity, clone repositories and trigger synchronisation
        without leaving Jungle Lab Studio.
      </p>

      <div className="project-layout">
        <aside className="project-list">
          <div className="project-list-header">
            <span>Configured projects</span>
            <button type="button" onClick={() => setSelectedId(null)}>
              ＋ New
            </button>
          </div>

          {sortedProjects.length === 0 ? (
            <div className="project-empty">No projects configured yet</div>
          ) : (
            <ul>
              {sortedProjects.map((project) => (
                <li
                  key={project.id}
                  className={selectedId === project.id ? 'active' : ''}
                >
                  <button type="button" onClick={() => setSelectedId(project.id)}>
                    <strong>{project.name}</strong>
                    <span>{project.repoUrl}</span>
                    <span className="project-branch">{project.defaultBranch}</span>
                    <span className="project-sync-status">
                      {project.lastSyncStatus || 'idle'}
                    </span>
                  </button>
                  <div className="project-actions">
                    <button type="button" onClick={() => handleSync(project.id)} disabled={isBusy}>
                      Sync
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteProject(project.id)}
                      disabled={isBusy}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <section className="project-form">
          <form onSubmit={handleSave} className="project-form-fields">
            <div className="setting-group">
              <label className="setting-label">
                <span>Project name</span>
                <input
                  type="text"
                  className="setting-input"
                  value={formState.name}
                  onChange={(event) => handleChange('name', event.target.value)}
                />
              </label>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Repository URL</span>
                <input
                  type="text"
                  className="setting-input"
                  value={formState.repoUrl}
                  onChange={(event) => handleChange('repoUrl', event.target.value)}
                  placeholder="https://github.com/owner/repo.git"
                />
              </label>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Local path</span>
                <input
                  type="text"
                  className="setting-input"
                  value={formState.localPath}
                  onChange={(event) => handleChange('localPath', event.target.value)}
                  placeholder="/projects/repo"
                />
              </label>
              <small className="setting-hint">
                Path on disk where the repository is or will be cloned.
              </small>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Default branch</span>
                <input
                  type="text"
                  className="setting-input"
                  value={formState.defaultBranch}
                  onChange={(event) => handleChange('defaultBranch', event.target.value)}
                />
              </label>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Personal access token</span>
                <input
                  type="password"
                  className="setting-input"
                  value={formState.personalAccessToken || ''}
                  onChange={(event) =>
                    handleChange('personalAccessToken', event.target.value)
                  }
                  placeholder="Optional, used for private repositories"
                />
              </label>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Auto sync cron</span>
                <input
                  type="text"
                  className={`setting-input ${cronError ? 'has-error' : ''}`}
                  value={formState.autoSyncCron || ''}
                  onChange={(event) => handleChange('autoSyncCron', event.target.value)}
                  placeholder="e.g. 0 */2 * * *"
                />
              </label>
              <small className="setting-hint">
                Optional. Automatically pulls the repository using the cron engine.
              </small>
              {cronError && <div className="form-error">{cronError}</div>}
              {nextSync && (
                <div className="project-next-run">
                  Next scheduled sync: {nextSync.toLocaleString()}
                </div>
              )}
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Description</span>
                <textarea
                  className="setting-textarea"
                  value={formState.description || ''}
                  onChange={(event) => handleChange('description', event.target.value)}
                  rows={3}
                />
              </label>
            </div>

            <div className="project-meta">
              <div>
                <strong>Last sync:</strong> {formatSyncStatus(projects.find((p) => p.id === formState.id))}
              </div>
              {formState.repoUrl && (
                <a
                  href={formState.repoUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="project-link"
                >
                  Open repository ↗
                </a>
              )}
            </div>

            {feedback && <div className="project-feedback">{feedback}</div>}

            <div className="project-actions-row">
              <button type="submit" className="primary-button" disabled={isBusy}>
                Save project
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={handleValidate}
                disabled={isBusy || !formState.repoUrl}
              >
                Validate
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={handleClone}
                disabled={isBusy || !formState.repoUrl || !formState.localPath}
              >
                Clone
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={handleSync}
                disabled={isBusy || !formState.id}
              >
                Sync now
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
};
