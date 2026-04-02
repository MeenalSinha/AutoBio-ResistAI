import React from 'react';
import {
  Pill, AlertCircle, CheckCircle2, AlertTriangle,
  ChevronRight, Info, ShieldAlert, Stethoscope
} from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Alert from '../components/Alert.jsx';
import styles from './TreatmentPage.module.css';

const STATUS_STYLE = {
  Resistant:    { color: '#dc2626', bg: '#fef2f2', Icon: AlertCircle   },
  Susceptible:  { color: '#0d9467', bg: '#ecfdf5', Icon: CheckCircle2  },
  Intermediate: { color: '#d97706', bg: '#fffbeb', Icon: AlertTriangle },
};

function DrugTag({ name, variant = 'blue' }) {
  return <span className={[styles.drugTag, styles[`drugTag_${variant}`]].join(' ')}>{name}</span>;
}

export default function TreatmentPage({ lastPrediction, onNavigate }) {
  if (!lastPrediction?.treatment) {
    return (
      <div className={styles.page}>
        <PageHeader title="Treatment Recommendations" description="Antibiotic guidance based on resistance prediction." />
        <Alert type="info" title="No prediction yet">
          Run a resistance prediction first. Treatment recommendations are generated automatically with each prediction.
        </Alert>
        <Button onClick={() => onNavigate('predict')} style={{ marginTop: 12 }}>
          Go to Predict
        </Button>
      </div>
    );
  }

  const { treatment, prediction } = lastPrediction;
  const st = STATUS_STYLE[treatment.status] || STATUS_STYLE.Intermediate;

  return (
    <div className={styles.page}>
      <PageHeader
        title="Treatment Recommendations"
        description="Evidence-based antibiotic stewardship guidance derived from the resistance prediction and detected resistance genes."
      />

      {/* Status banner */}
      <div className={styles.banner} style={{ background: st.bg, borderColor: st.color + '55' }}>
        <st.Icon size={24} style={{ color: st.color, flexShrink: 0 }} />
        <div className={styles.bannerContent}>
          <div className={styles.bannerTitle} style={{ color: st.color }}>
            Phenotype: {treatment.status}
          </div>
          <div className={styles.bannerUrgency}>{treatment.urgency}</div>
        </div>
        <div className={styles.bannerConf}>
          <div className={styles.confNum}>{(prediction.confidence * 100).toFixed(1)}%</div>
          <div className={styles.confLabel}>Model confidence</div>
        </div>
      </div>

      <div className={styles.grid}>
        {/* Primary recommendations */}
        <Card
          title="Recommended Antibiotics"
          subtitle="First-line and alternative options"
          badge="Clinical Guidance"
        >
          {treatment.primary_recommendations?.length > 0 && (
            <div className={styles.drugSection}>
              <div className={styles.drugSectionTitle}>
                <CheckCircle2 size={14} className={styles.greenIcon} />
                First-Line Options
              </div>
              <div className={styles.drugList}>
                {treatment.primary_recommendations.map(d => <DrugTag key={d} name={d} variant="green" />)}
              </div>
            </div>
          )}

          {treatment.alternative_recommendations?.length > 0 && (
            <div className={styles.drugSection}>
              <div className={styles.drugSectionTitle}>
                <ChevronRight size={14} className={styles.blueIcon} />
                Alternatives
              </div>
              <div className={styles.drugList}>
                {treatment.alternative_recommendations.map(d => <DrugTag key={d} name={d} variant="blue" />)}
              </div>
            </div>
          )}

          {treatment.last_resort_options?.length > 0 && (
            <div className={styles.drugSection}>
              <div className={styles.drugSectionTitle}>
                <ShieldAlert size={14} className={styles.redIcon} />
                Last Resort Only
              </div>
              <div className={styles.drugList}>
                {treatment.last_resort_options.map(d => <DrugTag key={d} name={d} variant="amber" />)}
              </div>
            </div>
          )}

          {treatment.drugs_to_avoid?.length > 0 && (
            <div className={styles.drugSection}>
              <div className={styles.drugSectionTitle}>
                <AlertCircle size={14} className={styles.redIcon} />
                Drugs to Avoid
              </div>
              <div className={styles.drugList}>
                {treatment.drugs_to_avoid.map(d => <DrugTag key={d} name={d} variant="red" />)}
              </div>
            </div>
          )}
        </Card>

        {/* Clinical notes */}
        <div className={styles.notesCol}>
          <Card title="Clinical Notes" subtitle="Actionable guidance for clinicians">
            <ul className={styles.noteList}>
              {treatment.clinical_notes?.map((note, i) => (
                <li key={i} className={styles.noteItem}>
                  <ChevronRight size={13} className={styles.noteArrow} />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </Card>

          <Card title="Antibiotic Stewardship" badge="Important">
            <p className={styles.stewardship}>{treatment.stewardship_note}</p>
          </Card>
        </div>
      </div>

      {/* Mechanism notes */}
      {treatment.mechanism_notes?.length > 0 && (
        <Card title="Resistance Mechanism Analysis" subtitle="Detected resistance determinants and their clinical implications">
          <div className={styles.mechList}>
            {treatment.mechanism_notes.map((note, i) => (
              <div key={i} className={styles.mechItem}>
                <div className={styles.mechDot} />
                <p>{note}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Resistance genes */}
      {treatment.resistance_genes_detected?.length > 0 && (
        <Card title="Resistance Genes Detected">
          <div className={styles.geneList}>
            {treatment.resistance_genes_detected.map(g => (
              <span key={g} className={styles.geneChip}>{g}</span>
            ))}
          </div>
        </Card>
      )}

      {/* Disclaimer */}
      <Alert type="warning" title="Clinical Disclaimer">
        These recommendations are generated by an AI model for research and educational purposes only.
        They are not a substitute for professional medical advice, clinical judgment, or local antibiogram data.
        Always confirm susceptibility with validated laboratory testing before initiating therapy.
      </Alert>
    </div>
  );
}
