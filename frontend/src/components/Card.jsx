import React from 'react';
import styles from './Card.module.css';

export default function Card({ title, subtitle, children, className = '', badge, badgeColor }) {
  return (
    <div className={[styles.card, className].join(' ')}>
      {(title || subtitle) && (
        <div className={styles.header}>
          <div>
            {title && <div className={styles.title}>{title}</div>}
            {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
          </div>
          {badge && (
            <span className={styles.badge} style={badgeColor ? { background: badgeColor + '18', color: badgeColor } : {}}>
              {badge}
            </span>
          )}
        </div>
      )}
      <div className={styles.body}>{children}</div>
    </div>
  );
}
