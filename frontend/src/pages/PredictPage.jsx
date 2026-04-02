import React, { useState } from 'react';
import { FlaskConical, Plus, Minus, AlertTriangle, CheckCircle2, AlertCircle } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import PageHeader from '../components/PageHeader.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Alert from '../components/Alert.jsx';
import { predictSample } from '../utils/api.js';
import styles from './PredictPage.module.css';

const DEFAULT_FEATURES = {
  mic_ampicillin:    8,
  mic_tetracycline:  4,
  mic_ciprofloxacin: 2,
  mic_gentamicin:    2,
  gene_blaTEM:       0,
  gene_mecA:         0,
  gene_vanA:         0,
  gene_qnrS:         0,
  gene_armA:         0,
};

const FEATURE_META = {
  mic_ampicillin:    { label: 'MIC Ampicillin (mg/L)',    type: 'number', min: 0, step: 0.5 },
  mic_tetracycline:  { label: 'MIC Tetracycline (mg/L)',  type: 'number', min: 0, step: 0.5 },
  mic_ciprofloxacin: { label: 'MIC Ciprofloxacin (mg/L)', type: 'number', min: 0, step: 0.25 },
  mic_gentamicin:    { label: 'MIC Gentamicin (mg/L)',    type: 'number', min: 0, step: 0.5 },
  gene_blaTEM:       { label: 'Gene blaTEM (present)',    type: 'toggle' },
  gene_mecA:         { label: 'Gene mecA (present)',      type: 'toggle' },
  gene_vanA:         { label: 'Gene vanA (present)',      type: 'toggle' },
  gene_qnrS:         { label: 'Gene qnrS (present)',      type: 'toggle' },
  gene_armA:         { label: 'Gene armA (present)',      type: 'toggle' },
};

const SPECIES_OPTIONS = [
  '', 'E. coli', 'K. pneumoniae', 'S. aureus', 'P. aeruginosa', 'A. baumannii', 'Other',
];

const RESISTANCE_STYLE = {
  Resistant:     { color: '#dc2626', bg: '#fef2f2', icon: AlertCircle  },
  Susceptible:   { color: '#0d9467', bg: '#ecfdf5', icon: CheckCircle2 },
  Intermediate:  { color: '#d97706', bg: '#fffbeb', icon: AlertTriangle },
};

export default function PredictPage({ trainedData, setPrediction, lastPrediction, onNavigate }) {
  const [features, setFeatures] = useState({ ...DEFAULT_FEATURES });
  const [species, setSpecies]   = useState('');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  const [result, setResult]     = useState(null);

  if (!trainedData) {
    return (
      <div className={styles.page}>
        <Alert type="warning" title="No model trained">
          Please train the AutoBio Engine first before making predictions.
        </Alert>
        <Button onClick={() => onNavigate('train')} style={{marginTop:12}}>Go to Training</Button>
      </div>
    );
  }

  const setFeature = (key, val) => setFeatures(f => ({ ...f, [key]: val }));

  const handlePredict = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await predictSample(features, species || undefined);
      setResult(res.data);
      setPrediction(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed.');
    } finally {
      setLoading(false);
    }
  };

  const radarData = Object.entries(features)
    .filter(([k]) => k.startsWith('mic_'))
    .map(([k, v]) => ({
      subject: k.replace('mic_', '').replace('_', ' '),
      value:   Math.min(Number(v), 32),
    }));

  const prediction = result?.prediction;
  const pStyle = prediction ? RESISTANCE_STYLE[prediction.prediction] || RESISTANCE_STYLE.Intermediate : null;

  return (
    <div className={styles.page}>
      <PageHeader
        title="Resistance Prediction"
        description="Enter bacterial features to predict resistance phenotype. Confidence scores and treatment recommendations are generated automatically."
      />

      <div className={styles.grid}>
        {/* Input form */}
        <Card title="Bacterial Features">
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Species (optional)</div>
            <select
              className={styles.select}
              value={species}
              onChange={e => setSpecies(e.target.value)}
            >
              {SPECIES_OPTIONS.map(s => <option key={s} value={s}>{s || 'Unknown / Not specified'}</option>)}
            </select>
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>MIC Values</div>
            <div className={styles.fields}>
              {Object.entries(FEATURE_META)
                .filter(([, m]) => m.type === 'number')
                .map(([key, meta]) => (
                  <div key={key} className={styles.field}>
                    <label className={styles.fieldLabel}>{meta.label}</label>
                    <div className={styles.numInput}>
                      <button className={styles.numBtn} onClick={() => setFeature(key, Math.max(0, +features[key] - meta.step))}>
                        <Minus size={12} />
                      </button>
                      <input
                        type="number"
                        className={styles.numVal}
                        value={features[key]}
                        min={meta.min}
                        step={meta.step}
                        onChange={e => setFeature(key, +e.target.value)}
                      />
                      <button className={styles.numBtn} onClick={() => setFeature(key, +(+features[key] + meta.step).toFixed(2))}>
                        <Plus size={12} />
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Resistance Genes</div>
            <div className={styles.genes}>
              {Object.entries(FEATURE_META)
                .filter(([, m]) => m.type === 'toggle')
                .map(([key, meta]) => (
                  <label key={key} className={styles.geneToggle}>
                    <input
                      type="checkbox"
                      checked={features[key] === 1}
                      onChange={e => setFeature(key, e.target.checked ? 1 : 0)}
                    />
                    <span className={[styles.geneCheck, features[key] ? styles.geneChecked : ''].join(' ')}>
                      {features[key] ? <CheckCircle2 size={13}/> : null}
                    </span>
                    <span className={styles.geneName}>{meta.label}</span>
                  </label>
                ))}
            </div>
          </div>

          <Button onClick={handlePredict} loading={loading} size="lg" className={styles.predictBtn}>
            <FlaskConical size={16} />
            {loading ? 'Analyzing...' : 'Predict Resistance'}
          </Button>

          {error && <Alert type="error" className={styles.mt}>{error}</Alert>}
        </Card>

        {/* MIC radar */}
        <Card title="MIC Profile" subtitle="Visualisation of minimum inhibitory concentrations">
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e4e7ef" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#4b5563' }} />
              <Radar dataKey="value" stroke="#1a56db" fill="#1a56db" fillOpacity={0.15} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
          <div className={styles.radarNote}>
            MIC values capped at 32 mg/L for visualisation
          </div>
        </Card>
      </div>

      {/* Prediction result */}
      {prediction && (
        <div
          className={styles.resultBanner}
          style={{ background: pStyle.bg, borderColor: pStyle.color + '44' }}
        >
          <pStyle.icon size={28} style={{ color: pStyle.color, flexShrink: 0 }} />
          <div>
            <div className={styles.resultLabel} style={{ color: pStyle.color }}>
              {prediction.prediction}
            </div>
            <div className={styles.resultConf}>
              Confidence: {(prediction.confidence * 100).toFixed(1)}% &nbsp;|&nbsp; Model: {trainedData.best_model}
            </div>
            <div className={styles.probRow}>
              {Object.entries(prediction.probabilities).map(([cls, prob]) => (
                <div key={cls} className={styles.probItem}>
                  <div className={styles.probLabel}>{cls}</div>
                  <div className={styles.probBar}>
                    <div
                      className={styles.probFill}
                      style={{
                        width: `${(prob * 100).toFixed(1)}%`,
                        background: RESISTANCE_STYLE[cls]?.color || '#6b7280',
                      }}
                    />
                  </div>
                  <div className={styles.probPct}>{(prob * 100).toFixed(1)}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Local explanation */}
      {result?.explanation?.top_contributing_features?.length > 0 && (
        <Card title="Feature Contributions" subtitle="SHAP values for this prediction — positive values increase predicted resistance">
          <div className={styles.shapList}>
            {result.explanation.top_contributing_features.slice(0, 8).map((f, i) => {
              const isPos = f.shap_value >= 0;
              const maxAbs = Math.max(
                ...result.explanation.top_contributing_features.map(x => Math.abs(x.shap_value))
              );
              const pct = maxAbs > 0 ? (Math.abs(f.shap_value) / maxAbs) * 100 : 0;
              return (
                <div key={i} className={styles.shapRow}>
                  <div className={styles.shapFeature}>{f.feature}</div>
                  <div className={styles.shapBarWrap}>
                    <div
                      className={styles.shapBar}
                      style={{
                        width: `${pct}%`,
                        background: isPos ? '#dc2626' : '#0d9467',
                      }}
                    />
                  </div>
                  <div className={styles.shapVal} style={{ color: isPos ? '#dc2626' : '#0d9467' }}>
                    {isPos ? '+' : ''}{f.shap_value.toFixed(4)}
                  </div>
                  <div className={styles.shapDir}>{f.direction}</div>
                </div>
              );
            })}
          </div>

          <Button
            variant="ghost"
            size="sm"
            className={styles.mt}
            onClick={() => onNavigate('explain')}
          >
            View Global Feature Importance
          </Button>
        </Card>
      )}

      {/* Navigate to treatment */}
      {result?.treatment && (
        <Card
          title="Treatment Recommendation"
          subtitle={`Status: ${result.treatment.status}`}
          badge={result.treatment.urgency}
          badgeColor={
            result.treatment.status === 'Resistant'    ? '#dc2626' :
            result.treatment.status === 'Susceptible'  ? '#0d9467' : '#d97706'
          }
        >
          <div className={styles.treatRow}>
            <div>
              <div className={styles.treatLabel}>Primary Recommendations</div>
              <div className={styles.drugList}>
                {result.treatment.primary_recommendations?.map(d => (
                  <span key={d} className={styles.drugTag}>{d}</span>
                ))}
              </div>
            </div>
            {result.treatment.drugs_to_avoid?.length > 0 && (
              <div>
                <div className={styles.treatLabel}>Avoid</div>
                <div className={styles.drugList}>
                  {result.treatment.drugs_to_avoid.map(d => (
                    <span key={d} className={styles.drugTagRed}>{d}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className={styles.mt}
            onClick={() => onNavigate('treatment')}
          >
            Full Treatment Details
          </Button>
        </Card>
      )}
    </div>
  );
}
