import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5605';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const adminApi = {
  getOperators: () => api.get('/api/admin/operators'),
  getOperator: (personId) => api.get(`/api/admin/operators/${personId}`),
  updateOperator: (personId, data) => api.put(`/api/admin/operators/${personId}`, data),
  pauseOperator: (personId, data) => api.post(`/api/admin/operators/${personId}/pause`, data),
  resumeOperator: (personId) => api.post(`/api/admin/operators/${personId}/resume`),
  createOperator: (data) => api.post('/api/admin/operators/create', data),
  
  createSchedule: (data) => api.post('/api/admin/schedules', data),
  updateSchedule: (scheduleId, data) => api.put(`/api/admin/schedules/${scheduleId}`, data),
  deleteSchedule: (scheduleId) => api.delete(`/api/admin/schedules/${scheduleId}`),
  
  resetCounters: (data) => api.post('/api/admin/assignment/reset', data),
  getAssignmentStats: () => api.get('/api/admin/assignment/stats'),
  
  getSystemConfig: (category) => api.get('/api/admin/config', { params: { category } }),
  getConfigValue: (key) => api.get(`/api/admin/config/${key}`),
  updateConfig: (key, data) => api.put(`/api/admin/config/${key}`, data),
  
  getAuditLogs: (params) => api.get('/api/admin/audit', { params }),
  
  getDashboardStats: () => api.get('/api/admin/dashboard/stats'),
  getOperatorMetrics: (personId, days) => api.get(`/api/admin/metrics/operator/${personId}`, { params: { days } }),
};

export const systemApi = {
  getStatus: () => api.get('/api/system/status'),
  pause: (data) => api.post('/api/system/pause', data),
  resume: (data) => api.post('/api/system/resume', data),
};

export default api;
