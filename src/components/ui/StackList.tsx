import React from 'react';
import { Badge, BadgeTone } from './Badge';
import './StackList.css';

export interface StackListProps {
  /** Items rendered inside the list. */
  children: React.ReactNode;
  /** Reduce the vertical padding of each entry. */
  dense?: boolean;
  className?: string;
  role?: string;
}

export interface StackListItemBadge {
  id?: string | number;
  label: React.ReactNode;
  /** Optional explicit tone. Falls back to `accent` when {@link accent} is true. */
  tone?: BadgeTone;
  /** Compatibility flag to highlight the badge. */
  accent?: boolean;
}

export interface StackListItemProps {
  title: React.ReactNode;
  description?: React.ReactNode;
  meta?: React.ReactNode;
  badges?: StackListItemBadge[];
  children?: React.ReactNode;
  className?: string;
}

/** Vertical list for contextual summaries used throughout the sidebar. */
export const StackList: React.FC<StackListProps> = ({
  children,
  dense = false,
  className = '',
  role = 'list',
}) => {
  const classes = ['px-stack-list'];
  if (dense) {
    classes.push('px-stack-list--dense');
  }
  if (className) {
    classes.push(className);
  }

  return (
    <div className={classes.join(' ')} role={role}>
      {children}
    </div>
  );
};

export const StackListItem: React.FC<StackListItemProps> = ({
  title,
  description,
  meta,
  badges,
  children,
  className = '',
}) => {
  const classes = ['px-stack-list__item'];
  if (className) {
    classes.push(className);
  }

  const resolvedBadges = badges?.map(badge => ({
    ...badge,
    tone: badge.tone ?? (badge.accent ? 'accent' : 'default'),
  }));

  return (
    <div className={classes.join(' ')} role="listitem">
      <div className="px-stack-list__content">
        <strong className="px-stack-list__title">{title}</strong>
        {description && <span className="px-stack-list__description">{description}</span>}
        {meta && <span className="px-stack-list__meta">{meta}</span>}
      </div>
      {children}
      {resolvedBadges && resolvedBadges.length > 0 && (
        <div className="px-stack-list__badges">
          {resolvedBadges.map(badge => (
            <Badge key={String(badge.id ?? badge.label)} tone={badge.tone}>
              {badge.label}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
};
