import React from 'react';
import styles from './StatTile.module.css';

export default function StatTile({ label, value, sub, accent }) {
  return (
    <div className={styles.tile} style={accent ? { borderTopColor: accent } : {}}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{value}</div>
      {sub && <div className={styles.sub}>{sub}</div>}
    </div>
  );
}
