import React, { useEffect, useState } from 'react';
import { FlaskConical, Cpu, BarChart3, Pill, ArrowRight, Database, Shield, Activity } from 'lucide-react';
import PageHeader from '../components/PageHeader.jsx';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import { checkHealth } from '../utils/api.js';
import styles from './Dashboard.module.css';

const STEPS = [
  { num: '01', title: 'Upload Dataset',       desc: 'Load an AMR dataset (CSV/Excel) or use the built-in sample data.' },
  { num: '02', title: 'Run AutoBio Engine',   desc: 'System trains Logistic Regression, Random Forest, and XGBoost simultaneously.' },
  { num: '03', title: 'Auto Model Selection', desc: 'Best model is selected automatically based on weighted F1 score.' },
  { num: '04', title: 'Predict Resistance',   desc: 'Submit bacterial features and receive resistance prediction with confidence.' },
  { num: '05', title: 'Explain Predictions',  desc: 'SHAP values reveal which features drive resistance — with biological context.' },
  { num: '06', title: 'Get Treatment Advice', desc: 'Evidence-based antibiotic recommendations tailored to the prediction.' },
];

const FEATURES = [
  { icon: Cpu,       title: 'Self-Optimizing Engine',    desc: 'Automatically compares 3 ML models and selects the champion — no manual tuning required.' },
  { icon: BarChart3, title: 'SHAP Explainability',       desc: 'SHapley Additive exPlanations reveal exactly which resistance genes and MIC values drive each prediction.' },
  { icon: Pill,      title: 'Treatment Recommendations', desc: 'Maps resistance profiles and detected genes to actionable, species-specific antibiotic guidance.' },
  { icon: Shield,    title: 'Multi-class Classification', desc: 'Predicts Resistant, Susceptible, and Intermediate phenotypes with calibrated confidence scores.' },
];

export default function Dashboard({ trainedData, onNavigate }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth()
      .then(r => setHealth(r.data))
      .catch(() => setHealth({ status: 'error' }));
  }, []);

  return (
    <div className={styles.page}>
      <PageHeader
        title="AutoBio-ResistAI"
        description="A self-optimizing AI system for antibiotic resistance prediction, automated model selection, and clinical decision support."
        actions={
          <Button onClick={() => onNavigate('train')} size="md">
            <Cpu size={15} />
            Launch Engine
          </Button>
        }
      />

      {/* API status */}
      {health && (
        <div className={[styles.apiStatus, health.status === 'ok' ? styles.apiOk : styles.apiErr].join(' ')}>
          <Activity size={14} />
          <span>
            API {health.status === 'ok' ? 'connected' : 'unreachable'} —&nbsp;
            {health.is_trained
              ? `Model ready (${health.model})`
              : 'No model trained yet'}
          </span>
        </div>
      )}

      {/* Hero cards */}
      <div className={styles.heroGrid}>
        <div className={styles.heroCard}>
          <div className={styles.heroIcon}><FlaskConical size={28} /></div>
          <div className={styles.heroNum}>3</div>
          <div className={styles.heroLabel}>ML Models Compared</div>
        </div>
        <div className={styles.heroCard}>
          <div className={styles.heroIcon}><Database size={28} /></div>
          <div className={styles.heroNum}>AMR</div>
          <div className={styles.heroLabel}>Resistance Datasets</div>
        </div>
        <div className={styles.heroCard}>
          <div className={styles.heroIcon}><BarChart3 size={28} /></div>
          <div className={styles.heroNum}>SHAP</div>
          <div className={styles.heroLabel}>Explainability</div>
        </div>
        <div className={styles.heroCard}>
          <div className={styles.heroIcon}><Pill size={28} /></div>
          <div className={styles.heroNum}>Auto</div>
          <div className={styles.heroLabel}>Treatment Guidance</div>
        </div>
      </div>

      {/* Demo flow */}
      <Card title="Demo Flow" subtitle="Step-by-step walkthrough of the system">
        <div className={styles.steps}>
          {STEPS.map((s, i) => (
            <div key={i} className={styles.step}>
              <div className={styles.stepNum}>{s.num}</div>
              <div className={styles.stepContent}>
                <div className={styles.stepTitle}>{s.title}</div>
                <div className={styles.stepDesc}>{s.desc}</div>
              </div>
              {i < STEPS.length - 1 && <ArrowRight size={16} className={styles.stepArrow} />}
            </div>
          ))}
        </div>
      </Card>

      {/* Key features */}
      <div className={styles.featGrid}>
        {FEATURES.map((f, i) => (
          <Card key={i} className={styles.featCard}>
            <div className={styles.featIcon}><f.icon size={20} /></div>
            <div className={styles.featTitle}>{f.title}</div>
            <div className={styles.featDesc}>{f.desc}</div>
          </Card>
        ))}
      </div>

      {/* Dataset info */}
      <Card title="Recommended Datasets" subtitle="Use these AMR datasets for best results">
        <div className={styles.datasetList}>
          <div className={styles.dataset}>
            <div className={styles.datasetName}>Mendeley AMR Dataset (Primary)</div>
            <div className={styles.datasetDesc}>Antibiotic susceptibility testing results — bacterial isolates with R/S/I outcomes.</div>
            <a href="https://data.mendeley.com/datasets/ccmrx8n7mk/1" target="_blank" rel="noreferrer" className={styles.datasetLink}>
              data.mendeley.com <ArrowRight size={12} />
            </a>
          </div>
          <div className={styles.dataset}>
            <div className={styles.datasetName}>Kaggle Multi-Resistance Dataset (Secondary)</div>
            <div className={styles.datasetDesc}>Multi-drug resistance profiles with bacterial strain identifiers and susceptibility outcomes.</div>
            <a href="https://www.kaggle.com/datasets/adilimadeddinehosni/multi-resistance-antibiotic-susceptibility" target="_blank" rel="noreferrer" className={styles.datasetLink}>
              kaggle.com <ArrowRight size={12} />
            </a>
          </div>
          <div className={styles.dataset}>
            <div className={styles.datasetName}>CARD Database (Optional)</div>
            <div className={styles.datasetDesc}>Curated resistance genes, mechanisms, and antibiotic associations for gene-level insights.</div>
            <a href="https://card.mcmaster.ca/download" target="_blank" rel="noreferrer" className={styles.datasetLink}>
              card.mcmaster.ca <ArrowRight size={12} />
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}
