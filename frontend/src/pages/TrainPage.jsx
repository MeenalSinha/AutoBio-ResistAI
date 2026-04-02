import React, { useState } from 'react';
import {
  Upload, Cpu, CheckCircle2, AlertCircle, ChevronDown, ChevronUp,
  Trophy, Clock, Table2
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend
} from 'recharts';
import PageHeader from '../components/PageHeader.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Alert from '../components/Alert.jsx';
import StatTile from '../components/StatTile.jsx';
import { uploadDataset, trainModels } from '../utils/api.js';
import styles from './TrainPage.module.css';

const METRIC_COLORS = {
  accuracy:  '#1a56db',
  precision: '#0d9467',
  recall:    '#d97706',
  f1_score:  '#7c3aed',
};

export default function TrainPage({ trainedData, setTrained, onNavigate }) {
  const [file, setFile]             = useState(null);
  const [uploadInfo, setUploadInfo] = useState(null);
  const [useSample, setUseSample]   = useState(false);
  const [targetCol, setTargetCol]   = useState('');
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [log, setLog]               = useState([]);
  const [showReport, setShowReport] = useState(false);

  const appendLog = (msg) => setLog(l => [...l, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const handleFileChange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setError('');
    try {
      appendLog(`Uploading ${f.name}...`);
      const res = await uploadDataset(f);
      setUploadInfo(res.data);
      appendLog(`Uploaded: ${res.data.rows} rows, ${res.data.columns} columns detected.`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    }
  };

  const handleTrain = async () => {
    setLoading(true);
    setError('');
    setLog([]);
    try {
      appendLog('Initialising AutoBio Engine...');
      appendLog('Preprocessing dataset (imputation, encoding, scaling)...');
      appendLog('Training Logistic Regression...');
      appendLog('Training Random Forest (200 estimators)...');
      appendLog('Training XGBoost (200 rounds)...');
      appendLog('Running 5-fold cross-validation...');
      appendLog('Evaluating hold-out test set...');

      const res = await trainModels({
        target_column:   targetCol,
        test_size:       0.2,
        cv_folds:        5,
        use_sample_data: useSample || !uploadInfo,
      });

      setTrained(res.data);
      appendLog(`Best model selected: ${res.data.best_model}`);
      appendLog(`F1 Score: ${res.data.best_model_metrics.f1_score}`);
      appendLog('SHAP explainer fitted on training background.');
      appendLog('Training complete.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Training failed. Check backend logs.');
      appendLog('ERROR: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const chartData = trainedData?.model_comparison?.map(m => ({
    name:      m.model === 'Logistic Regression' ? 'Log. Reg.' : m.model,
    Accuracy:  +(m.accuracy  * 100).toFixed(1),
    Precision: +(m.precision * 100).toFixed(1),
    Recall:    +(m.recall    * 100).toFixed(1),
    'F1 Score':+(m.f1_score  * 100).toFixed(1),
  }));

  return (
    <div className={styles.page}>
      <PageHeader
        title="Train AutoBio Engine"
        description="Upload your AMR dataset or use sample data. The engine trains three models, evaluates them, and selects the best automatically."
      />

      {/* Upload */}
      <Card title="Dataset Configuration">
        <div className={styles.configGrid}>
          <div>
            <label className={styles.label}>Upload Dataset (CSV / Excel)</label>
            <label className={styles.fileZone}>
              <Upload size={20} className={styles.uploadIcon} />
              <span>{file ? file.name : 'Click to select file'}</span>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileChange} hidden />
            </label>
            {uploadInfo && (
              <div className={styles.uploadMeta}>
                {uploadInfo.rows} rows · {uploadInfo.columns} columns
              </div>
            )}
          </div>

          <div className={styles.orDivider}>
            <span>or</span>
          </div>

          <div>
            <label className={styles.label}>Use Built-in Sample Data</label>
            <label className={styles.toggle}>
              <input
                type="checkbox"
                checked={useSample}
                onChange={e => setUseSample(e.target.checked)}
              />
              <span className={styles.toggleTrack}>
                <span className={styles.toggleThumb} />
              </span>
              <span className={styles.toggleLabel}>
                {useSample ? 'Enabled — verified AMR sample dataset' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>

        {uploadInfo && (
          <div className={styles.colSelector}>
            <label className={styles.label}>Target Column (leave blank for auto-detection)</label>
            <select
              className={styles.select}
              value={targetCol}
              onChange={e => setTargetCol(e.target.value)}
            >
              <option value="">Auto-detect</option>
              {uploadInfo.column_info.map(c => (
                <option key={c.name} value={c.name}>{c.name} ({c.dtype})</option>
              ))}
            </select>
          </div>
        )}

        <div className={styles.trainActions}>
          <Button onClick={handleTrain} loading={loading} size="lg">
            <Cpu size={16} />
            {loading ? 'Training...' : 'Run AutoBio Engine'}
          </Button>
          {trainedData && (
            <Button variant="ghost" onClick={() => onNavigate('predict')}>
              Go to Predictions
            </Button>
          )}
        </div>

        {error && <Alert type="error" className={styles.mt}>{error}</Alert>}
      </Card>

      {/* Training log */}
      {log.length > 0 && (
        <Card title="Training Log" badge={loading ? 'Running' : 'Complete'} badgeColor={loading ? '#d97706' : '#0d9467'}>
          <div className={styles.logBox}>
            {log.map((l, i) => <div key={i} className={styles.logLine}>{l}</div>)}
            {loading && <div className={styles.logCursor}>_</div>}
          </div>
        </Card>
      )}

      {/* Results */}
      {trainedData && (
        <>
          {/* Best model banner */}
          <div className={styles.bestBanner}>
            <Trophy size={18} className={styles.trophyIcon} />
            <div>
              <div className={styles.bestTitle}>Best Model Selected: {trainedData.best_model}</div>
              <div className={styles.bestSub}>
                Auto-selected based on highest weighted F1 score on hold-out test set
              </div>
            </div>
          </div>

          {/* Metrics */}
          <div className={styles.metricsGrid}>
            <StatTile
              label="Accuracy"
              value={`${(trainedData.best_model_metrics.accuracy * 100).toFixed(1)}%`}
              sub="Hold-out test set"
              accent="#1a56db"
            />
            <StatTile
              label="F1 Score (Weighted)"
              value={`${(trainedData.best_model_metrics.f1_score * 100).toFixed(1)}%`}
              sub="Selection criterion"
              accent="#7c3aed"
            />
            <StatTile
              label="Precision"
              value={`${(trainedData.best_model_metrics.precision * 100).toFixed(1)}%`}
              sub="Weighted average"
              accent="#0d9467"
            />
            <StatTile
              label="Recall"
              value={`${(trainedData.best_model_metrics.recall * 100).toFixed(1)}%`}
              sub="Weighted average"
              accent="#d97706"
            />
            <StatTile
              label="CV F1 Mean"
              value={`${(trainedData.best_model_metrics.cv_f1_mean * 100).toFixed(1)}%`}
              sub={`+/- ${(trainedData.best_model_metrics.cv_f1_std * 100).toFixed(1)}%`}
              accent="#0891b2"
            />
            <StatTile
              label="Training Time"
              value={`${trainedData.best_model_metrics.training_time_s}s`}
              sub="Best model"
              accent="#6b7280"
            />
          </div>

          {/* Model comparison chart */}
          <Card title="Model Comparison" subtitle="All three models evaluated on the same hold-out test set (%)">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 13, fill: '#4b5563' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#9ca3af' }} tickFormatter={v => `${v}%`} />
                <Tooltip formatter={(v) => `${v}%`} contentStyle={{ borderRadius: 8, border: '1px solid #e4e7ef', fontSize: 13 }} />
                <Legend wrapperStyle={{ fontSize: 13 }} />
                <Bar dataKey="Accuracy"  fill={METRIC_COLORS.accuracy}  radius={[3,3,0,0]} />
                <Bar dataKey="Precision" fill={METRIC_COLORS.precision} radius={[3,3,0,0]} />
                <Bar dataKey="Recall"    fill={METRIC_COLORS.recall}    radius={[3,3,0,0]} />
                <Bar dataKey="F1 Score"  fill={METRIC_COLORS.f1_score}  radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Model comparison table */}
          <Card title="Detailed Comparison Table">
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Accuracy</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1 Score</th>
                    <th>CV F1</th>
                    <th>Time (s)</th>
                  </tr>
                </thead>
                <tbody>
                  {trainedData.model_comparison.map((m) => (
                    <tr key={m.model} className={m.is_best ? styles.bestRow : ''}>
                      <td>
                        {m.is_best && <Trophy size={12} className={styles.rowTrophy} />}
                        {m.model}
                      </td>
                      <td>{(m.accuracy  * 100).toFixed(1)}%</td>
                      <td>{(m.precision * 100).toFixed(1)}%</td>
                      <td>{(m.recall    * 100).toFixed(1)}%</td>
                      <td className={styles.bold}>{(m.f1_score  * 100).toFixed(1)}%</td>
                      <td>{(m.cv_f1_mean * 100).toFixed(1)}% ± {(m.cv_f1_std * 100).toFixed(1)}%</td>
                      <td>{m.training_time_s}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Confusion matrix image */}
          {trainedData.confusion_matrix_chart && (
            <Card title="Confusion Matrix" subtitle={`${trainedData.best_model} — test set`}>
              <img
                src={`data:image/png;base64,${trainedData.confusion_matrix_chart}`}
                alt="Confusion Matrix"
                className={styles.chartImg}
              />
            </Card>
          )}

          {/* Gene Network Image */}
          {trainedData.gene_network_chart && (
            <Card title="Resistance Gene Network" subtitle="Co-occurrence & correlation visualization (Hackathon Requirement)">
              <img
                src={`data:image/png;base64,${trainedData.gene_network_chart}`}
                alt="Resistance Gene Network"
                className={styles.chartImg}
              />
            </Card>
          )}

          {/* Dataset info */}
          <Card title="Dataset Info">
            <div className={styles.infoGrid}>
              {Object.entries(trainedData.dataset_info).map(([k, v]) => {
                if (typeof v === 'object') return null;
                return (
                  <div key={k} className={styles.infoItem}>
                    <div className={styles.infoLabel}>{k.replace(/_/g, ' ')}</div>
                    <div className={styles.infoVal}>{String(v)}</div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Classification report */}
          <Card
            title="Classification Report"
            subtitle="Per-class precision, recall, F1"
            badge={showReport ? 'Hide' : 'Show'}
          >
            <button className={styles.toggleReport} onClick={() => setShowReport(s => !s)}>
              {showReport ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
              {showReport ? 'Collapse' : 'Expand report'}
            </button>
            {showReport && (
              <div className={styles.tableWrap} style={{marginTop:12}}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Class</th>
                      <th>Precision</th>
                      <th>Recall</th>
                      <th>F1 Score</th>
                      <th>Support</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(trainedData.classification_report)
                      .filter(([k]) => !['accuracy','macro avg','weighted avg'].includes(k))
                      .map(([cls, metrics]) => (
                        <tr key={cls}>
                          <td className={styles.bold}>{cls}</td>
                          <td>{(metrics.precision * 100).toFixed(1)}%</td>
                          <td>{(metrics.recall    * 100).toFixed(1)}%</td>
                          <td>{(metrics['f1-score']*100).toFixed(1)}%</td>
                          <td>{metrics.support}</td>
                        </tr>
                      ))
                    }
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
