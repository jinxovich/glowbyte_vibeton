import axios from 'axios';
import type {
  PredictionRequest,
  PredictionResponse,
  Metrics,
  DashboardData,
  CalendarItem,
  HealthResponse,
} from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const healthCheck = async (): Promise<HealthResponse> => {
  const { data } = await api.get('/health');
  return data;
};

export const predict = async (
  records: PredictionRequest[]
): Promise<PredictionResponse[]> => {
  const { data } = await api.post('/predict', { records });
  return data;
};

export const trainModel = async (force: boolean = false) => {
  const { data } = await api.post('/train', { force });
  return data;
};

export const getHistory = async () => {
  const { data } = await api.get('/history');
  return data;
};

export const getMetrics = async (): Promise<Metrics> => {
  const { data } = await api.get('/api/metrics');
  return data;
};

export const getDashboard = async (): Promise<DashboardData> => {
  const { data } = await api.get('/api/dashboard');
  return data;
};

export const getCalendar = async (): Promise<CalendarItem[]> => {
  const { data } = await api.get('/api/calendar');
  return data;
};

export const getStockpileDetails = async (storageId: string, stackId: string) => {
  const { data } = await api.get(`/api/stockpile/${storageId}/${stackId}`);
  return data;
};

export default api;

