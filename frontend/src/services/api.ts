import axios from 'axios';

// API base URL - use environment variable or default to relative path
// When running in Vite dev server, use relative URLs to leverage the proxy
// In production or when VITE_API_BASE_URL is explicitly set, use that
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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

// Utility function to extract error message from FastAPI responses
export const getErrorMessage = (error: any): string => {
  if (error.response) {
    const errorData = error.response.data;
    
    // Handle FastAPI validation errors (422) - detail is an array
    if (Array.isArray(errorData?.detail)) {
      return errorData.detail
        .map((err: any) => {
          const field = err.loc?.slice(1).join('.') || 'field';
          return `${field}: ${err.msg}`;
        })
        .join(', ');
    } else if (errorData?.detail) {
      // Single error message
      return errorData.detail;
    } else if (errorData?.message) {
      return errorData.message;
    } else {
      return `Server error: ${error.response.status}`;
    }
  } else if (error.request) {
    return 'Cannot connect to server. Make sure the backend is running on http://localhost:8000';
  } else {
    return error.message || 'An unexpected error occurred';
  }
};

// Handle token refresh on 401 and log errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log error for debugging
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('Network Error: No response from server. Is the backend running?');
    } else {
      console.error('Error:', error.message);
    }
    
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
