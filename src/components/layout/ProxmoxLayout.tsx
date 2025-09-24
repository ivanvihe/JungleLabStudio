import React from 'react';
import './ProxmoxLayout.css';

interface ProxmoxShellProps {
  children: React.ReactNode;
  className?: string;
}

export const ProxmoxShell: React.FC<ProxmoxShellProps> = ({ children, className }) => {
  const classes = ['proxmox-shell'];
  if (className) {
    classes.push(className);
  }

  return <div className={classes.join(' ')}>{children}</div>;
};

interface SidebarProps {
  title: string;
  subtitle?: string;
  toolbar?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  title,
  subtitle,
  toolbar,
  footer,
  children,
  className,
}) => {
  const classes = ['proxmox-sidebar'];
  if (className) {
    classes.push(className);
  }

  return (
    <aside className={classes.join(' ')}>
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <span className="sidebar-title">{title}</span>
          {subtitle && <span className="sidebar-subtitle">{subtitle}</span>}
        </div>
        {toolbar && <div className="sidebar-toolbar">{toolbar}</div>}
      </div>
      <div className="sidebar-content">{children}</div>
      {footer && <div className="sidebar-footer">{footer}</div>}
    </aside>
  );
};

interface MainChatProps {
  header?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const MainChat: React.FC<MainChatProps> = ({ header, children, className }) => {
  const classes = ['proxmox-mainchat'];
  if (className) {
    classes.push(className);
  }

  return (
    <section className={classes.join(' ')}>
      {header && <div className="mainchat-header">{header}</div>}
      <div className="mainchat-body">{children}</div>
    </section>
  );
};

interface CollapsiblePanelProps {
  title: string;
  collapsed?: boolean;
  onToggle?: () => void;
  toolbar?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

export const TaskActivityPanel: React.FC<CollapsiblePanelProps> = ({
  title,
  collapsed,
  onToggle,
  toolbar,
  children,
  className,
}) => {
  const classes = ['proxmox-task-panel'];
  if (collapsed) {
    classes.push('collapsed');
  }
  if (className) {
    classes.push(className);
  }

  return (
    <aside className={classes.join(' ')}>
      <div className="panel-header">
        <span className="panel-title">{title}</span>
        <div className="panel-actions">
          {toolbar}
          {onToggle && (
            <button
              type="button"
              className="panel-toggle"
              onClick={onToggle}
              aria-label={collapsed ? 'Expandir panel de tareas' : 'Colapsar panel de tareas'}
              aria-expanded={!collapsed}
            >
              {collapsed ? '⤢' : '⤡'}
            </button>
          )}
        </div>
      </div>
      <div className="panel-body">{children}</div>
    </aside>
  );
};

interface FooterPanelProps {
  title: string;
  collapsed?: boolean;
  onToggle?: () => void;
  toolbar?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

export const FooterPanel: React.FC<FooterPanelProps> = ({
  title,
  collapsed,
  onToggle,
  toolbar,
  children,
  className,
}) => {
  const classes = ['proxmox-footer'];
  if (collapsed) {
    classes.push('collapsed');
  }
  if (className) {
    classes.push(className);
  }

  return (
    <footer className={classes.join(' ')}>
      <div className="panel-header">
        <span className="panel-title">{title}</span>
        <div className="panel-actions">
          {toolbar}
          {onToggle && (
            <button
              type="button"
              className="panel-toggle"
              onClick={onToggle}
              aria-label={collapsed ? 'Expandir panel inferior' : 'Colapsar panel inferior'}
              aria-expanded={!collapsed}
            >
              {collapsed ? '▲' : '▼'}
            </button>
          )}
        </div>
      </div>
      <div className="panel-body">{children}</div>
    </footer>
  );
};
