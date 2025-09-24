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
  navigation?: React.ReactNode;
}

export const Sidebar: React.FC<SidebarProps> = ({
  title,
  subtitle,
  toolbar,
  footer,
  children,
  className,
  navigation,
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
      <div className="sidebar-scroll">
        {navigation && (
          <div className="sidebar-navigation">
            <div className="sidebar-navigation__inner">{navigation}</div>
          </div>
        )}
        <div className="sidebar-content">{children}</div>
      </div>
      {footer && <div className="sidebar-footer">{footer}</div>}
    </aside>
  );
};

interface MainChatProps {
  header?: React.ReactNode;
  title?: string;
  subtitle?: string;
  status?: React.ReactNode;
  toolbar?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export const MainChat: React.FC<MainChatProps> = ({
  header,
  title,
  subtitle,
  status,
  toolbar,
  actions,
  children,
  footer,
  className,
}) => {
  const classes = ['proxmox-mainchat'];
  if (className) {
    classes.push(className);
  }

  const resolvedHeader = header ?? (
    <MainChatHeader
      title={title}
      subtitle={subtitle}
      status={status}
      toolbar={toolbar}
      actions={actions}
    />
  );

  return (
    <section className={classes.join(' ')}>
      {resolvedHeader && <div className="mainchat-header">{resolvedHeader}</div>}
      <div className="mainchat-body">
        <div className="mainchat-scroll">{children}</div>
        {footer && <div className="mainchat-footer">{footer}</div>}
      </div>
    </section>
  );
};

interface MainChatHeaderProps {
  title?: string;
  subtitle?: string;
  status?: React.ReactNode;
  actions?: React.ReactNode;
  toolbar?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
  className?: string;
}

export const MainChatHeader: React.FC<MainChatHeaderProps> = ({
  title,
  subtitle,
  status,
  actions,
  toolbar,
  breadcrumbs,
  className,
}) => {
  if (!title && !subtitle && !status && !toolbar && !actions && !breadcrumbs) {
    return null;
  }

  const classes = ['mainchat-header__inner'];
  if (className) {
    classes.push(className);
  }

  return (
    <div className={classes.join(' ')}>
      <div className="mainchat-header__headline">
        <div className="mainchat-header__titles">
          {breadcrumbs && <div className="mainchat-header__breadcrumbs">{breadcrumbs}</div>}
          {title && <h1 className="mainchat-header__title">{title}</h1>}
          {subtitle && <p className="mainchat-header__subtitle">{subtitle}</p>}
        </div>
        <div className="mainchat-header__side">
          {status && <div className="mainchat-header__status">{status}</div>}
          {actions && <div className="mainchat-header__actions">{actions}</div>}
        </div>
      </div>
      {toolbar && <div className="mainchat-header__toolbar">{toolbar}</div>}
    </div>
  );
};

interface ChatSearchBarProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  suffix?: React.ReactNode;
}

export const ChatSearchBar: React.FC<ChatSearchBarProps> = ({ icon, suffix, ...props }) => {
  return (
    <div className="chat-search">
      {icon && <span className="chat-search__icon">{icon}</span>}
      <input className="chat-search__input" {...props} />
      {suffix && <span className="chat-search__suffix">{suffix}</span>}
    </div>
  );
};

interface ChatMessageListProps {
  children: React.ReactNode;
  className?: string;
}

export const ChatMessageList: React.FC<ChatMessageListProps> = ({ children, className }) => {
  const classes = ['chat-thread'];
  if (className) {
    classes.push(className);
  }

  return <div className={classes.join(' ')}>{children}</div>;
};

interface ChatMessageProps {
  author: string;
  role?: 'user' | 'assistant' | 'system';
  timestamp: string;
  content: React.ReactNode;
  variant?: 'inbound' | 'outbound';
  avatar?: React.ReactNode;
  meta?: React.ReactNode;
  actions?: React.ReactNode;
  status?: React.ReactNode;
  attachments?: React.ReactNode;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  author,
  role = 'user',
  timestamp,
  content,
  variant = 'inbound',
  avatar,
  meta,
  actions,
  status,
  attachments,
}) => {
  const classes = ['chat-message', `chat-message--${variant}`, `chat-message--${role}`];

  return (
    <article className={classes.join(' ')}>
      {avatar && <div className="chat-message__avatar">{avatar}</div>}
      <div className="chat-message__bubble">
        <header className="chat-message__header">
          <div className="chat-message__identity">
            <span className="chat-message__author">{author}</span>
            <span className="chat-message__timestamp">{timestamp}</span>
            {meta && <span className="chat-message__meta">{meta}</span>}
          </div>
          {actions && <div className="chat-message__actions">{actions}</div>}
        </header>
        <div className="chat-message__content">{content}</div>
        {attachments && <div className="chat-message__attachments">{attachments}</div>}
        {status && <footer className="chat-message__status">{status}</footer>}
      </div>
    </article>
  );
};

interface ChatTimelineMarkerProps {
  label: string;
  icon?: React.ReactNode;
}

export const ChatTimelineMarker: React.FC<ChatTimelineMarkerProps> = ({ label, icon }) => (
  <div className="chat-marker">
    {icon && <span className="chat-marker__icon">{icon}</span>}
    <span className="chat-marker__label">{label}</span>
  </div>
);

export interface PanelTabDescriptor {
  id: string;
  label: string;
  badge?: string | number;
  content: React.ReactNode;
}

interface CollapsiblePanelProps {
  title: string;
  collapsed?: boolean;
  onToggle?: () => void;
  toolbar?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  tabs?: PanelTabDescriptor[];
  defaultTabId?: string;
  onTabChange?: (tabId: string) => void;
}

export const TaskActivityPanel: React.FC<CollapsiblePanelProps> = ({
  title,
  collapsed,
  onToggle,
  toolbar,
  children,
  className,
  tabs,
  defaultTabId,
  onTabChange,
}) => {
  const classes = ['proxmox-task-panel'];
  if (collapsed) {
    classes.push('collapsed');
  }
  if (className) {
    classes.push(className);
  }

  const [activeTab, setActiveTab] = React.useState(() => {
    if (tabs && tabs.length > 0) {
      return defaultTabId && tabs.some(tab => tab.id === defaultTabId)
        ? defaultTabId
        : tabs[0].id;
    }
    return '';
  });

  React.useEffect(() => {
    if (!tabs || tabs.length === 0) return;
    const fallback = defaultTabId && tabs.some(tab => tab.id === defaultTabId)
      ? defaultTabId
      : tabs[0].id;
    if (!activeTab || !tabs.some(tab => tab.id === activeTab)) {
      setActiveTab(fallback);
    }
  }, [tabs, defaultTabId, activeTab]);

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId);
    onTabChange?.(tabId);
  };

  const renderPanelBody = () => {
    if (!tabs || tabs.length === 0) {
      return children;
    }

    const current = tabs.find(tab => tab.id === activeTab) ?? tabs[0];

    return (
      <div className="panel-tabs">
        <div className="panel-tablist" role="tablist" aria-label={title}>
          {tabs.map(tab => {
            const tabClasses = ['panel-tab'];
            if (tab.id === current.id) {
              tabClasses.push('is-active');
            }
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                className={tabClasses.join(' ')}
                aria-selected={tab.id === current.id}
                onClick={() => handleTabClick(tab.id)}
              >
                <span className="panel-tab__label">{tab.label}</span>
                {tab.badge !== undefined && tab.badge !== null && (
                  <span className="panel-tab__badge">{tab.badge}</span>
                )}
              </button>
            );
          })}
        </div>
        <div className="panel-tabpanes" role="tabpanel">
          {current.content}
        </div>
      </div>
    );
  };

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
      <div className="panel-body">{renderPanelBody()}</div>
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

export interface SidebarNavItem {
  id: string;
  icon: React.ReactNode;
  label: string;
  description?: string;
  badge?: string | number;
}

export interface SidebarNavSection {
  id: string;
  title?: string;
  items: SidebarNavItem[];
}

interface SidebarNavigationProps {
  sections: SidebarNavSection[];
  activeId: string;
  onSelect: (itemId: string) => void;
  className?: string;
}

export const SidebarNavigation: React.FC<SidebarNavigationProps> = ({
  sections,
  activeId,
  onSelect,
  className,
}) => {
  const classes = ['sidebar-nav'];
  if (className) {
    classes.push(className);
  }

  return (
    <nav className={classes.join(' ')}>
      {sections.map(section => (
        <div key={section.id} className="sidebar-nav__section">
          {section.title && <span className="sidebar-nav__title">{section.title}</span>}
          <div className="sidebar-nav__items">
            {section.items.map(item => {
              const itemClasses = ['sidebar-nav__item'];
              if (item.id === activeId) {
                itemClasses.push('is-active');
              }
              return (
                <button
                  key={item.id}
                  type="button"
                  className={itemClasses.join(' ')}
                  onClick={() => onSelect(item.id)}
                >
                  <span className="sidebar-nav__icon">{item.icon}</span>
                  <span className="sidebar-nav__content">
                    <span className="sidebar-nav__label">{item.label}</span>
                    {item.description && (
                      <span className="sidebar-nav__description">{item.description}</span>
                    )}
                  </span>
                  {item.badge !== undefined && item.badge !== null && (
                    <span className="sidebar-nav__badge">{item.badge}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
};
