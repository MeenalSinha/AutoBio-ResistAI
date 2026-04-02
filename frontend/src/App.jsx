import React, { useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import TrainPage from './pages/TrainPage.jsx';
import PredictPage from './pages/PredictPage.jsx';
import ExplainPage from './pages/ExplainPage.jsx';
import TreatmentPage from './pages/TreatmentPage.jsx';
import styles from './App.module.css';

const PAGES = {
  dashboard:  Dashboard,
  train:      TrainPage,
  predict:    PredictPage,
  explain:    ExplainPage,
  treatment:  TreatmentPage,
};

export default function App() {
  const [page, setPage]           = useState('dashboard');
  const [trainedData, setTrained] = useState(null);   // results from /train
  const [lastPrediction, setPred] = useState(null);   // results from /predict

  const PageComponent = PAGES[page] || Dashboard;

  return (
    <div className={styles.shell}>
      <Sidebar currentPage={page} onNavigate={setPage} isTrained={!!trainedData} />
      <main className={styles.main}>
        <PageComponent
          trainedData={trainedData}
          setTrained={setTrained}
          lastPrediction={lastPrediction}
          setPrediction={setPred}
          onNavigate={setPage}
        />
      </main>
    </div>
  );
}
