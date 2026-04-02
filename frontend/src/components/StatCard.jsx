import React from 'react';
import styles from './StatCard.module.css';

export default function StatCard({ label, value, sub, color, icon: Icon }) {
  return (
    <div className={styles.card} style={color ? { '--accent': color } : {}}>
      <div className={styles.top}>
        <span className={styles.label}>{label}</span>
        {Icon && (
          <span className={styles.iconWrap}>
            <Icon size={15} />
          </span>
        )}
      </div>
      <div className={styles.value}>{value}</div>
      {sub && <div className={styles.sub}>{sub}</div>}
    </div>
  );
}
