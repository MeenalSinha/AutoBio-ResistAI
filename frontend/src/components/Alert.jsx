import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';
import styles from './Alert.module.css';

const MAP = {
  error:   { icon: AlertCircle,   cls: styles.error   },
  success: { icon: CheckCircle2,  cls: styles.success },
  info:    { icon: Info,          cls: styles.info    },
  warning: { icon: AlertTriangle, cls: styles.warning },
};

export default function Alert({ type = 'info', title, children }) {
  const { icon: Icon, cls } = MAP[type] || MAP.info;
  return (
    <div className={[styles.alert, cls].join(' ')}>
      <Icon size={16} className={styles.icon} />
      <div className={styles.content}>
        {title && <div className={styles.title}>{title}</div>}
        {children && <div className={styles.body}>{children}</div>}
      </div>
    </div>
  );
}
