import React from 'react';
import './SidebarCard.css';

export interface SidebarCardProps {
  title: string;
  subtitle?: string;
  description?: React.ReactNode;
  meta?: React.ReactNode;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

/**
 * Card layout tailored for the Proxmox style sidebar panels.
 * Groups related summaries together with optional description and footer slots.
 */
export const SidebarCard: React.FC<SidebarCardProps> = ({
  title,
  subtitle,
  description,
  meta,
  children,
  footer,
  className = '',
}) => {
  const classes = ['px-sidebar-card'];
  if (className) {
    classes.push(className);
  }

  return (
    <section className={classes.join(' ')}>
      <header className="px-sidebar-card__header">
        {subtitle && <span className="px-sidebar-card__subtitle">{subtitle}</span>}
        <h2 className="px-sidebar-card__title">{title}</h2>
      </header>
      <div className="px-sidebar-card__body">
        {description && <p className="px-sidebar-card__meta">{description}</p>}
        {meta && <p className="px-sidebar-card__meta">{meta}</p>}
        {children}
      </div>
      {footer && <footer className="px-sidebar-card__footer">{footer}</footer>}
    </section>
  );
};

export default SidebarCard;
