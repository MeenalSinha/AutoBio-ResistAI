import React, { useState, useEffect } from 'react';
import { BarChart3, RefreshCw, Info } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell
} from 'recharts';
import PageHeader from '../components/PageHeader.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Alert from '../components/Alert.jsx';
import { getGlobalExplanation } from '../utils/api.js';
import styles from './ExplainPage.module.css';

export default function ExplainPage({ trainedData, onNavigate }) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [maxFeat, setMaxFeat] = useState(15);

  if (!trainedData) {
    return (
      <div className={styles.page}>
        <Alert type="warning" title="No model trained">
          Train the AutoBio Engine first to access explainability.
        </Alert>
        <Button onClick={() => onNavigate('train')} style={{ marginTop: 12 }}>Go to Training</Button>
      </div>
    );
  }

  const fetchExplanation = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getGlobalExplanation(maxFeat);
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load explanations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchExplanation(); }, []);

  const chartData = data?.top_features?.map(f => ({
    feature:    f.feature,
    importance: +f.importance.toFixed(5),
  })) || [];

  const maxVal = chartData.length ? Math.max(...chartData.map(d => d.importance)) : 1;

  return (
    <div className={styles.page}>
      <PageHeader
        title="Model Explainability"
        description="SHAP (SHapley Additive exPlanations) reveal which bacterial features most strongly drive antibiotic resistance predictions."
        actions={
          <div className={styles.controls}>
            <label className={styles.label}>Top features</label>
            <select
              className={styles.select}
              value={maxFeat}
              onChange={e => setMaxFeat(+e.target.value)}
            >
              {[5, 10, 15, 20].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
            <Button variant="secondary" size="sm" onClick={fetchExplanation} loading={loading}>
              <RefreshCw size={13} />
              Refresh
            </Button>
          </div>
        }
      />

      {error && <Alert type="error">{error}</Alert>}

      {/* SHAP explanation text */}
      {data?.explanation && (
        <Alert type="info" title="About SHAP">
          {data.explanation}
        </Alert>
      )}

      {/* SHAP image (from backend) */}
      {data?.chart_base64 && (
        <Card title="Global Feature Importance" subtitle={`Top ${maxFeat} features by mean |SHAP value|`}>
          <img
            src={`data:image/png;base64,${data.chart_base64}`}
            alt="SHAP Feature Importance"
            className={styles.shapImg}
          />
        </Card>
      )}

      {/* Interactive chart */}
      {chartData.length > 0 && (
        <Card title="Feature Importance — Interactive" subtitle="Hover for exact values">
          <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 26)}>
            <BarChart
              data={[...chartData].reverse()}
              layout="vertical"
              margin={{ top: 0, right: 60, left: 140, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} tickFormatter={v => v.toFixed(4)} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 12, fill: '#4b5563' }} width={136} />
              <Tooltip
                formatter={(v) => [v.toFixed(5), 'Mean |SHAP|']}
                contentStyle={{ borderRadius: 8, border: '1px solid #e4e7ef', fontSize: 13 }}
              />
              <Bar dataKey="importance" radius={[0, 3, 3, 0]}>
                {[...chartData].reverse().map((entry, idx) => (
                  <Cell
                    key={idx}
                    fill={entry.importance === maxVal ? '#1a56db' : '#93c5fd'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Feature interpretation table */}
      {data?.top_features?.length > 0 && (
        <Card title="Biological Interpretation" subtitle="What each top feature means in the context of AMR">
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Feature</th>
                  <th>Importance</th>
                  <th>Biological Context</th>
                </tr>
              </thead>
              <tbody>
                {data.top_features.map((f, i) => (
                  <tr key={f.feature} className={i === 0 ? styles.topRow : ''}>
                    <td className={styles.rank}>#{i + 1}</td>
                    <td>
                      <span className={styles.featureName}>{f.feature}</span>
                      <span className={styles.featureCategory}>
                        {f.feature.startsWith('gene_') ? 'Genotypic' : f.feature.startsWith('mic_') ? 'Phenotypic' : 'Metadata'}
                      </span>
                    </td>
                    <td>
                      <div className={styles.impCell}>
                        <div className={styles.impBar}>
                          <div
                            className={styles.impFill}
                            style={{ width: `${(f.importance / maxVal * 100).toFixed(0)}%` }}
                          />
                        </div>
                        <span className={styles.impVal}>{f.importance.toFixed(5)}</span>
                      </div>
                    </td>
                    <td className={styles.interp}>{f.interpretation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Model info */}
      <Card title="Explainability Method" subtitle="Technical details">
        <div className={styles.methodGrid}>
          <div className={styles.methodItem}>
            <div className={styles.methodLabel}>Method</div>
            <div className={styles.methodVal}>SHAP (SHapley Additive exPlanations)</div>
          </div>
          <div className={styles.methodItem}>
            <div className={styles.methodLabel}>Explainer Type</div>
            <div className={styles.methodVal}>
              {trainedData.best_model === 'Logistic Regression'
                ? 'KernelExplainer (model-agnostic)'
                : 'TreeExplainer (exact, fast)'}
            </div>
          </div>
          <div className={styles.methodItem}>
            <div className={styles.methodLabel}>Best Model</div>
            <div className={styles.methodVal}>{trainedData.best_model}</div>
          </div>
          <div className={styles.methodItem}>
            <div className={styles.methodLabel}>Interpretation</div>
            <div className={styles.methodVal}>Higher value = stronger influence on resistance classification</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
