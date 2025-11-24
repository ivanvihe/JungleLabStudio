import React, { useEffect, useMemo, useState } from 'react';
import { CronJob } from '../../types/automation';
import { getNextRun, validateCronExpression } from '../../utils/cron';
import './AutomationSettings.css';

interface AutomationSettingsProps {
  cronJobs: CronJob[];
  onSaveJob: (job: CronJob) => void;
  onDeleteJob: (jobId: string) => void;
  onToggleJob: (jobId: string, enabled: boolean) => void;
  onRunJob: (jobId: string) => void;
}

type FormState = {
  id?: string;
  name: string;
  cronExpression: string;
  command: string;
  workingDirectory: string;
  enabled: boolean;
};

const defaultFormState: FormState = {
  name: '',
  cronExpression: '*/5 * * * *',
  command: '',
  workingDirectory: '',
  enabled: true
};

function createId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `cron-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function formatDate(value?: string): string {
  if (!value) {
    return '—';
  }
  try {
    return new Date(value).toLocaleString();
  } catch (error) {
    return value;
  }
}

function formatNextRun(expression: string): string {
  const next = getNextRun(expression);
  if (!next) {
    return 'Not scheduled';
  }
  return next.toLocaleString();
}

export const AutomationSettings: React.FC<AutomationSettingsProps> = ({
  cronJobs,
  onSaveJob,
  onDeleteJob,
  onToggleJob,
  onRunJob
}) => {
  const userJobs = useMemo(
    () => cronJobs.filter((job) => job.source !== 'project'),
    [cronJobs]
  );

  const projectJobs = useMemo(
    () => cronJobs.filter((job) => job.source === 'project'),
    [cronJobs]
  );

  const [selectedId, setSelectedId] = useState<string | null>(
    userJobs.length > 0 ? userJobs[0].id : null
  );
  const [formState, setFormState] = useState<FormState>(defaultFormState);
  const [cronError, setCronError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedId) {
      setFormState(defaultFormState);
      setCronError(null);
      return;
    }
    const job = userJobs.find((item) => item.id === selectedId);
    if (job) {
      setFormState({
        id: job.id,
        name: job.name,
        cronExpression: job.cronExpression,
        command: job.command,
        workingDirectory: job.workingDirectory || '',
        enabled: job.enabled
      });
      setCronError(null);
    }
  }, [selectedId, userJobs]);

  useEffect(() => {
    if (userJobs.length === 0) {
      setSelectedId(null);
    }
  }, [userJobs.length]);

  const handleFieldChange = <K extends keyof FormState>(
    key: K,
    value: FormState[K]
  ) => {
    setFormState((prev) => ({ ...prev, [key]: value }));
    if (key === 'cronExpression') {
      setCronError(null);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const error = validateCronExpression(formState.cronExpression);
    if (error) {
      setCronError(error);
      return;
    }

    const id = formState.id || createId();
    const job: CronJob = {
      id,
      name: formState.name.trim() || `Cron ${id.slice(-4)}`,
      cronExpression: formState.cronExpression.trim(),
      command: formState.command.trim(),
      workingDirectory: formState.workingDirectory.trim() || undefined,
      enabled: formState.enabled,
      source: 'user'
    };

    const existing = cronJobs.find((item) => item.id === id);
    if (existing) {
      job.lastRunAt = existing.lastRunAt;
      job.lastStatus = existing.lastStatus;
      job.lastOutput = existing.lastOutput;
      job.lastError = existing.lastError;
    }

    onSaveJob(job);
    setSelectedId(id);
    setSaveMessage('Cron job saved');
    window.setTimeout(() => setSaveMessage(null), 2500);
  };

  const handleAddNew = () => {
    setSelectedId(null);
    setFormState(defaultFormState);
    setCronError(null);
  };

  const handleDelete = (jobId: string) => {
    if (!window.confirm('Delete this cron job?')) {
      return;
    }
    onDeleteJob(jobId);
    if (selectedId === jobId) {
      setSelectedId(null);
    }
  };

  return (
    <div className="automation-settings">
      <h3>🕒 Automation & Cron Jobs</h3>
      <p className="setting-description">
        Configure recurring tasks that will execute shell commands on schedule. The
        scheduler runs in the background while the application is open.
      </p>

      <div className="automation-layout">
        <div className="automation-sidebar">
          <div className="automation-sidebar-header">
            <span>Custom jobs</span>
            <button type="button" onClick={handleAddNew}>
              ＋ Add
            </button>
          </div>

          {userJobs.length === 0 ? (
            <div className="automation-empty">No cron jobs yet</div>
          ) : (
            <ul className="automation-job-list">
              {userJobs.map((job) => (
                <li
                  key={job.id}
                  className={job.id === selectedId ? 'active' : ''}
                >
                  <button type="button" onClick={() => setSelectedId(job.id)}>
                    <span className="job-name">{job.name}</span>
                    <span className={`job-status ${job.enabled ? 'enabled' : 'disabled'}`}>
                      {job.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                    <span className="job-expression">{job.cronExpression}</span>
                    <span className="job-next-run">
                      Next run: {formatNextRun(job.cronExpression)}
                    </span>
                  </button>
                  <div className="job-actions">
                    <button type="button" onClick={() => onRunJob(job.id)}>
                      Run now
                    </button>
                    <button type="button" onClick={() => handleDelete(job.id)}>
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {projectJobs.length > 0 && (
            <div className="automation-projects">
              <h4>Project jobs</h4>
              <p>
                Managed automatically from project settings. They stay enabled while
                the project has auto-sync configured.
              </p>
              <ul>
                {projectJobs.map((job) => (
                  <li key={job.id}>
                    <div>
                      <strong>{job.name}</strong>
                      <span>{job.cronExpression}</span>
                    </div>
                    <div className="project-job-actions">
                      <button type="button" onClick={() => onRunJob(job.id)}>
                        Run now
                      </button>
                      <span className={`job-status ${job.enabled ? 'enabled' : 'disabled'}`}>
                        {job.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="automation-form">
          <form onSubmit={handleSubmit} className="automation-form-fields">
            <div className="setting-group">
              <label className="setting-label">
                <span>Name</span>
                <input
                  type="text"
                  value={formState.name}
                  onChange={(event) => handleFieldChange('name', event.target.value)}
                  className="setting-input"
                  placeholder="Describe this job"
                />
              </label>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Cron expression</span>
                <input
                  type="text"
                  value={formState.cronExpression}
                  onChange={(event) => handleFieldChange('cronExpression', event.target.value)}
                  className={`setting-input ${cronError ? 'has-error' : ''}`}
                />
              </label>
              <small className="setting-hint">
                Format: minute hour day month weekday. Example every 15 minutes:
                <code>*/15 * * * *</code>
              </small>
              {cronError && <div className="form-error">{cronError}</div>}
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Command</span>
                <textarea
                  value={formState.command}
                  onChange={(event) => handleFieldChange('command', event.target.value)}
                  className="setting-textarea"
                  placeholder="Command to execute"
                  rows={3}
                />
              </label>
              <small className="setting-hint">
                Commands run using the system shell when available. In preview builds
                the execution is simulated.
              </small>
            </div>

            <div className="setting-group">
              <label className="setting-label">
                <span>Working directory</span>
                <input
                  type="text"
                  value={formState.workingDirectory}
                  onChange={(event) =>
                    handleFieldChange('workingDirectory', event.target.value)
                  }
                  className="setting-input"
                  placeholder="Optional path"
                />
              </label>
              <small className="setting-hint">
                Leave empty to run the command in the application directory.
              </small>
            </div>

            <div className="setting-group inline">
              <label className="setting-checkbox">
                <input
                  type="checkbox"
                  checked={formState.enabled}
                  onChange={(event) =>
                    handleFieldChange('enabled', event.target.checked)
                  }
                />
                <span>Enable job</span>
              </label>
              {saveMessage && <span className="save-message">{saveMessage}</span>}
            </div>

            <div className="setting-group">
              <div className="automation-meta">
                <div>
                  <strong>Last run:</strong> {formatDate(formState.id ? cronJobs.find((job) => job.id === formState.id)?.lastRunAt : undefined)}
                </div>
                <div>
                  <strong>Next run:</strong>{' '}
                  {formState.cronExpression
                    ? formatNextRun(formState.cronExpression)
                    : 'Not scheduled'}
                </div>
              </div>
            </div>

            <div className="automation-actions">
              <button type="submit" className="primary-button">
                Save changes
              </button>
              {formState.id && (
                <>
                  <button
                    type="button"
                    onClick={() => onRunJob(formState.id!)}
                    className="secondary-button"
                  >
                    Run now
                  </button>
                  <button
                    type="button"
                    onClick={() => onToggleJob(formState.id!, !formState.enabled)}
                    className="secondary-button"
                  >
                    {formState.enabled ? 'Disable' : 'Enable'}
                  </button>
                </>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
