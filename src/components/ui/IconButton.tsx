import React from 'react';
import './IconButton.css';

/**
 * Icon-first button with Proxmox-inspired styling.
 *
 * Designed for toolbar and chrome controls where an accessible label is still required.
 */
export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Icon element rendered inside the button. Should be decorative only.
   */
  icon: React.ReactNode;
  /**
   * Human readable label announced to assistive tech and used as tooltip fallback.
   */
  label: string;
  /** Visual treatment for the button. */
  variant?: 'default' | 'accent' | 'danger' | 'ghost';
  /** Control the overall size of the button. */
  size?: 'sm' | 'md';
  /** Whether the button should appear toggled on. */
  isActive?: boolean;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  label,
  variant = 'default',
  size = 'md',
  isActive = false,
  className = '',
  title,
  type,
  ...props
}) => {
  const classes = ['px-icon-button', `px-icon-button--${variant}`, `px-icon-button--${size}`];
  if (isActive) {
    classes.push('is-active');
  }
  if (className) {
    classes.push(className);
  }

  return (
    <button
      {...props}
      type={type ?? 'button'}
      className={classes.join(' ')}
      aria-label={label}
      title={title ?? label}
    >
      <span aria-hidden="true" className="px-icon-button__icon">
        {icon}
      </span>
    </button>
  );
};

export default IconButton;
