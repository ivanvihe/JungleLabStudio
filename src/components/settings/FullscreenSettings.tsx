import React from 'react';

interface MonitorInfo {
  id: string;
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  isPrimary: boolean;
  scaleFactor: number;
}

interface FullscreenSettingsProps {
  monitors: MonitorInfo[];
  monitorRoles: Record<string, 'main' | 'secondary' | 'none'>;
  onMonitorRoleChange: (id: string, role: 'main' | 'secondary' | 'none') => void;
}

export const FullscreenSettings: React.FC<FullscreenSettingsProps> = ({
  monitors,
  monitorRoles,
  onMonitorRoleChange,
}) => {
  return (
    <div className="settings-section">
      <h3>🖥️ Configuración de Monitores</h3>

      <div className="monitors-grid">
        {monitors.map((monitor) => (
          <div key={monitor.id} className="monitor-card">
            <div className="monitor-preview">
              <div className="monitor-screen">
                <span className="monitor-resolution">
                  {monitor.size.width}×{monitor.size.height}
                </span>
                {monitor.isPrimary && <span className="primary-badge">Principal</span>}
              </div>
            </div>

            <div className="monitor-info">
              <h4>{monitor.label}</h4>
              <div className="monitor-details">
                <span>Posición: {monitor.position.x}, {monitor.position.y}</span>
                <span>Escala: {monitor.scaleFactor}x</span>
              </div>

              <div className="monitor-role">
                <span>Rol:</span>
                <select
                  value={monitorRoles[monitor.id] || 'none'}
                  onChange={(e) =>
                    onMonitorRoleChange(monitor.id, e.target.value as any)
                  }
                  className="setting-select"
                >
                  <option value="none">No usar</option>
                  <option value="main">Principal</option>
                  <option value="secondary">Secundario</option>
                </select>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="monitors-summary">
        <strong>
          Monitores en uso: {
            Object.values(monitorRoles).filter((r) => r !== 'none').length
          }
        </strong>
        <p>Configura un monitor principal y opcionalmente secundarios.</p>
      </div>
    </div>
  );
};

