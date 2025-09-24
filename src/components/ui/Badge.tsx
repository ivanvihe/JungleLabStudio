import React from 'react';
import './Badge.css';

/** Visual variants supported by the {@link Badge} component. */
export type BadgeTone = 'default' | 'accent' | 'muted' | 'success' | 'warning' | 'danger';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Optional leading icon, rendered before the label. */
  icon?: React.ReactNode;
  /** Controls the color treatment of the badge. */
  tone?: BadgeTone;
}

/**
 * Small status indicator used across the sidebar to highlight context and metadata.
 */
export const Badge: React.FC<BadgeProps> = ({
  icon,
  tone = 'default',
  className = '',
  children,
  ...props
}) => {
  const classes = ['px-badge', `px-badge--${tone}`];
  if (className) {
    classes.push(className);
  }

  return (
    <span {...props} className={classes.join(' ')}>
      {icon && (
        <span aria-hidden="true" className="px-badge__icon">
          {icon}
        </span>
      )}
      <span className="px-badge__label">{children}</span>
    </span>
  );
};

export default Badge;
