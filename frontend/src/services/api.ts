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

// ============= Corpus Types =============

export interface FingerprintSampleResponse {
  id: number;
  user_id: number;
  source_type: string;
  word_count: number;
  created_at: string;
  written_at: string | null;
  text_preview: string;
}

export interface CorpusStatus {
  sample_count: number;
  total_words: number;
  source_distribution: Record<string, number>;
  ready_for_fingerprint: boolean;
  samples_needed: number;
  oldest_sample: string | null;
  newest_sample: string | null;
}

export interface EnhancedFingerprintResponse {
  id: number;
  user_id: number;
  corpus_size: number;
  method: string;
  alpha: number;
  source_distribution: Record<string, number> | null;
  created_at: string;
  updated_at: string;
}

// Fingerprint Comparison Types
export interface ConfidenceInterval {
  lower: number;
  upper: number;
}

export interface FeatureDeviation {
  feature: string;
  text_value: number;
  fingerprint_value: number;
  deviation: number;
}

export interface FingerprintComparisonResponse {
  similarity: number;
  confidence_interval: ConfidenceInterval;
  match_level: 'HIGH' | 'MEDIUM' | 'LOW';
  feature_deviations: FeatureDeviation[];
  method_used: string;
  corpus_size?: number;
}

export interface FingerprintProfile {
  has_fingerprint: boolean;
  corpus_size?: number;
  method?: string;
  alpha?: number;
  source_distribution?: Record<string, number> | null;
  created_at?: string;
  updated_at?: string;
  feature_count: number;
}

// ============= Drift Detection Types =============

export type DriftSeverity = 'warning' | 'alert' | 'none';

export interface FeatureChange {
  feature: string;
  current_value: number;
  baseline_value: number;
  normalized_deviation: number;
}

export interface DriftDetectionResult {
  drift_detected: boolean;
  severity: DriftSeverity;
  similarity: number;
  baseline_mean: number;
  z_score: number;
  confidence_interval: [number, number];
  changed_features: FeatureChange[];
  timestamp?: string;
  reason?: string;
}

export interface DriftAlert {
  id: number;
  severity: DriftSeverity;
  similarity_score: number;
  baseline_similarity: number;
  z_score: number;
  changed_features: FeatureChange[];
  text_preview?: string;
  acknowledged: boolean;
  created_at: string;
}

export interface DriftAlertsList {
  alerts: DriftAlert[];
  total: number;
  unacknowledged_count: number;
}

export interface DriftBaselineResponse {
  status: string;
  mean: number;
  std: number;
  window_size: number;
  thresholds: {
    drift: number;
    alert: number;
  };
}

export interface DriftStatus {
  baseline_established: boolean;
  baseline_mean: number | null;
  baseline_std: number | null;
  current_window_size: number;
  thresholds: {
    drift: number;
    alert: number;
  };
  unacknowledged_alerts: number;
  last_check: string | null;
}

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
  analyze: async (
    text: string,
    granularity: 'sentence' | 'paragraph' = 'sentence'
  ) => {
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
  // Corpus management methods
  corpus: {
    add: async (text: string, sourceType: string = 'manual', writtenAt?: string): Promise<FingerprintSampleResponse> => {
      const response = await api.post('/api/fingerprint/corpus/add', {
        text_content: text,
        source_type: sourceType,
        written_at: writtenAt,
      });
      return response.data;
    },
    getStatus: async (): Promise<CorpusStatus> => {
      const response = await api.get('/api/fingerprint/corpus/status');
      return response.data;
    },
    getSamples: async (page: number = 1, pageSize: number = 20): Promise<FingerprintSampleResponse[]> => {
      const response = await api.get('/api/fingerprint/corpus/samples', {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    deleteSample: async (sampleId: number): Promise<void> => {
      await api.delete(`/api/fingerprint/corpus/sample/${sampleId}`);
    },
    generateFingerprint: async (method: string = 'time_weighted', alpha: number = 0.3): Promise<EnhancedFingerprintResponse> => {
      const response = await api.post('/api/fingerprint/corpus/generate', null, {
        params: { method, alpha },
      });
      return response.data;
    },
  },
  // Comparison methods
  compare: async (text: string, useEnhanced: boolean = true): Promise<FingerprintComparisonResponse> => {
    const response = await api.post('/api/fingerprint/compare', {
      text,
      use_enhanced: useEnhanced,
    });
    return response.data;
  },
  getProfile: async (): Promise<FingerprintProfile> => {
    const response = await api.get('/api/fingerprint/profile');
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

// Analytics API
export const analyticsAPI = {
  getOverview: async () => {
    const response = await api.get('/api/analytics/overview');
    return response.data;
  },
  getActivity: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/activity?days=${days}`);
    return response.data;
  },
  getTrends: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/trends?days=${days}`);
    return response.data;
  },
  getPerformance: async () => {
    const response = await api.get('/api/analytics/performance');
    return response.data;
  },
  getHistory: async (page: number = 1, pageSize: number = 20, search?: string, minProbability?: number, maxProbability?: number) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) params.append('search', search);
    if (minProbability !== undefined) params.append('min_probability', minProbability.toString());
    if (maxProbability !== undefined) params.append('max_probability', maxProbability.toString());

    const response = await api.get(`/api/analytics/history?${params.toString()}`);
    return response.data;
  },
};

// Batch Analysis API
export const batchAPI = {
  uploadBatch: async (files: File[] | FileList, granularity: 'sentence' | 'paragraph' = 'sentence') => {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('granularity', granularity);
    const response = await api.post('/api/batch/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  uploadBatchZip: async (zipFile: File, granularity: 'sentence' | 'paragraph' = 'sentence') => {
    const formData = new FormData();
    formData.append('zip_file', zipFile);
    formData.append('granularity', granularity);
    const response = await api.post('/api/batch/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  getBatchStatus: async (jobId: number) => {
    const response = await api.get(`/api/batch/${jobId}/status`);
    return response.data;
  },
  getBatchResults: async (jobId: number) => {
    const response = await api.get(`/api/batch/${jobId}/results`);
    return response.data;
  },
  exportBatch: async (jobId: number, format: 'csv' | 'json' = 'csv') => {
    const response = await api.get(`/api/batch/${jobId}/export?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  },
  listBatchJobs: async (skip: number = 0, limit: number = 50) => {
    const response = await api.get(`/api/batch/jobs?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  getDocumentDetail: async (jobId: number, documentId: number) => {
    const response = await api.get(`/api/batch/${jobId}/documents/${documentId}`);
    return response.data;
  },
};

// API Keys API
export const apiKeysAPI = {
  create: async (name: string, expires_in_days?: number) => {
    const response = await api.post('/api/keys', { name, expires_in_days });
    // Store the full key as it's only shown once
    if (response.data.key) {
      return response.data;
    }
    return response.data;
  },
  list: async () => {
    const response = await api.get('/api/keys');
    return response.data;
  },
  delete: async (keyId: number) => {
    const response = await api.delete(`/api/keys/${keyId}`);
    return response.data;
  },
};

// Usage API
export const usageAPI = {
  getUsage: async () => {
    const response = await api.get('/api/usage');
    return response.data;
  },
  getLimits: async () => {
    const response = await api.get('/api/limits');
    return response.data;
  },
};

// Drift Detection API
export const driftAPI = {
  // Get drift alerts for current user
  getAlerts: async (includeAcknowledged = false): Promise<DriftAlertsList> => {
    const response = await api.get('/api/fingerprint/drift/alerts', {
      params: { include_acknowledged: includeAcknowledged },
    });
    return response.data;
  },

  // Check text for style drift
  checkDrift: async (text: string, useEnhanced = true): Promise<DriftDetectionResult> => {
    const response = await api.post('/api/fingerprint/drift/check', {
      text,
      use_enhanced: useEnhanced,
    });
    return response.data;
  },

  // Acknowledge an alert
  acknowledgeAlert: async (alertId: number, updateBaseline = false): Promise<void> => {
    await api.post(`/api/fingerprint/drift/acknowledge/${alertId}`, null, {
      params: { update_baseline: updateBaseline },
    });
  },

  // Establish baseline manually
  establishBaseline: async (similarities: number[]): Promise<DriftBaselineResponse> => {
    const response = await api.post('/api/fingerprint/drift/baseline', similarities);
    return response.data;
  },

  // Get drift detector status
  getStatus: async (): Promise<DriftStatus> => {
    const response = await api.get('/api/fingerprint/drift/status');
    return response.data;
  },
};

export default api;
