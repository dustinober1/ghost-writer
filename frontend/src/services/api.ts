import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: async (email: string, password: string) => {
    const response = await api.post('/api/auth/register', { email, password });
    return response.data;
  },
  login: async (email: string, password: string) => {
    // Try JSON endpoint first, fallback to form data
    try {
      const response = await api.post('/api/auth/login-json', { email, password });
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
      }
      return response.data;
    } catch (err) {
      // Fallback to form data
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      const response = await api.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
      }
      return response.data;
    }
  },
  logout: () => {
    localStorage.removeItem('access_token');
  },
};

// Analysis API
export const analysisAPI = {
  analyze: async (text: string, granularity: 'sentence' | 'paragraph' = 'sentence') => {
    const response = await api.post('/api/analysis/analyze', { text, granularity });
    return response.data;
  },
};

// Fingerprint API
export const fingerprintAPI = {
  upload: async (text?: string, file?: File) => {
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    } else if (text) {
      formData.append('text', text);
    }
    const response = await api.post('/api/fingerprint/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getStatus: async () => {
    const response = await api.get('/api/fingerprint/status');
    return response.data;
  },
  generate: async () => {
    const response = await api.post('/api/fingerprint/generate');
    return response.data;
  },
  fineTune: async (newSamples: string[], weight: number = 0.3) => {
    const response = await api.post('/api/fingerprint/finetune', {
      new_samples: newSamples,
      weight,
    });
    return response.data;
  },
};

// Rewrite API
export const rewriteAPI = {
  rewrite: async (text: string, targetStyle?: string) => {
    const response = await api.post('/api/rewrite/rewrite', {
      text,
      target_style: targetStyle,
    });
    return response.data;
  },
  getHistory: async () => {
    const response = await api.get('/api/rewrite/history');
    return response.data;
  },
};

export default api;
