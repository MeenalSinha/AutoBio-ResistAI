import React from 'react';
import {
  LayoutDashboard, FlaskConical, Cpu, BarChart3,
  Pill, BookOpen, CheckCircle2
} from 'lucide-react';
import styles from './Sidebar.module.css';

const NAV = [
  { id: 'dashboard', label: 'Overview',        icon: LayoutDashboard },
  { id: 'train',     label: 'Train Engine',    icon: Cpu,    requiresNothing: true },
  { id: 'predict',   label: 'Predict',         icon: FlaskConical, requiresTrained: true },
  { id: 'explain',   label: 'Explainability',  icon: BarChart3,    requiresTrained: true },
  { id: 'treatment', label: 'Treatment',       icon: Pill,         requiresTrained: true },
];

export default function Sidebar({ currentPage, onNavigate, isTrained }) {
  return (
    <aside className={styles.sidebar}>
      {/* Logo */}
      <div className={styles.brand}>
        <div className={styles.brandIcon}>
          <FlaskConical size={20} />
        </div>
        <div>
          <div className={styles.brandName}>AutoBio-ResistAI</div>
          <div className={styles.brandSub}>Resistance Prediction</div>
        </div>
      </div>

      {/* Status badge */}
      <div className={styles.statusRow}>
        <span className={isTrained ? styles.statusBadgeOn : styles.statusBadgeOff}>
          <span className={isTrained ? styles.dotOn : styles.dotOff} />
          {isTrained ? 'Model ready' : 'Not trained'}
        </span>
      </div>

      {/* Nav */}
      <nav className={styles.nav}>
        {NAV.map(({ id, label, icon: Icon, requiresTrained }) => {
          const disabled = requiresTrained && !isTrained;
          const active   = currentPage === id;
          return (
            <button
              key={id}
              className={[
                styles.navItem,
                active    ? styles.active   : '',
                disabled  ? styles.disabled : '',
              ].join(' ')}
              onClick={() => !disabled && onNavigate(id)}
              title={disabled ? 'Train a model first' : label}
              disabled={disabled}
            >
              <Icon size={17} className={styles.navIcon} />
              <span>{label}</span>
              {active && <span className={styles.activeBar} />}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={styles.footer}>
        <div className={styles.footerLine}>AMR Prediction System</div>
        <div className={styles.footerLine}>v1.0.0</div>
      </div>
    </aside>
  );
}
