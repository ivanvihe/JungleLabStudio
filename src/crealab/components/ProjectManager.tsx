import React, { useRef, useState } from 'react';
import { CreaLabProject } from '../types/CrealabTypes';
import { ProjectSerializer } from '../core/ProjectSerializer';
import './ProjectManager.css';

interface ProjectManagerProps {
  project: CreaLabProject;
  onProjectLoad: (project: CreaLabProject) => void;
  onClose: () => void;
}

const ProjectManager: React.FC<ProjectManagerProps> = ({ project, onProjectLoad, onClose }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [backups, setBackups] = useState(ProjectSerializer.getAvailableBackups());
  const [error, setError] = useState<string | null>(null);

  const handleExport = () => {
    const data = ProjectSerializer.exportProject(project, 'json');
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project.name.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    file.text().then(text => {
      try {
        const imported = ProjectSerializer.deserialize(text);
        onProjectLoad(imported);
        setError(null);
        setBackups(ProjectSerializer.getAvailableBackups());
        onClose();
      } catch (err: any) {
        setError(err.message);
      }
    });
  };

  const handleRestore = (key: string) => {
    try {
      const restored = ProjectSerializer.restoreBackup(key);
      onProjectLoad(restored);
      setError(null);
      onClose();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const createBackup = () => {
    ProjectSerializer.createBackup(project);
    setBackups(ProjectSerializer.getAvailableBackups());
  };

  return (
    <div className="project-manager-overlay">
      <div className="project-manager">
        <h2>Project Manager</h2>
        <div className="pm-section">
          <button onClick={handleExport}>Export JSON</button>
          <button onClick={() => fileInputRef.current?.click()}>Import JSON</button>
          <input
            type="file"
            accept="application/json"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleImport}
          />
        </div>

        <div className="pm-section">
          <h3>Backups</h3>
          <button onClick={createBackup}>Create Backup</button>
          <ul className="backup-list">
            {backups.map(b => (
              <li key={b.key} className="backup-item">
                <span className="backup-info">{b.name} - {b.timestamp.toLocaleString()}</span>
                <button onClick={() => handleRestore(b.key)}>Restore</button>
              </li>
            ))}
            {backups.length === 0 && <li className="backup-item">No backups</li>}
          </ul>
        </div>

        {error && <div className="pm-error">{error}</div>}

        <div className="pm-actions">
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default ProjectManager;

