import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 min for training
});

export const checkHealth = () => api.get('/health');
export const getSampleData = () => api.get('/sample-data');
export const getModelInfo = () => api.get('/models/info');

export const uploadDataset = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const trainModels = (payload) => api.post('/train', payload);

export const getGlobalExplanation = (maxFeatures = 15) =>
  api.get(`/explain/global?max_features=${maxFeatures}`);

export const predictSample = (features, species) =>
  api.post('/predict', { features, species });

export const predictBatch = (file) => {
  const form = new FormData();
  form.append('file', file);
  return api.post('/predict/batch', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export default api;
