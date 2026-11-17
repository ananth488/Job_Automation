import axios from 'axios';
import { clearAuthCookie } from '@/lib/auth-cookie';
import type {
  AuthResponse,
  LoginCredentials,
  User,
  Resume,
  CandidateProfile,
  Preference,
  Job,
  JobMatch,
  Application,
  Notification,
  BotSettings,
  BotRun,
  DashboardStats,
  ChartData,
  RecentActivity,
} from '@/types';

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000/api/v1';
    }
  }
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined') {
    return 'https://job-automation-2-fe7i.onrender.com/api/v1';
  }
  return process.env.NODE_ENV === 'production'
    ? 'https://job-automation-2-fe7i.onrender.com/api/v1'
    : 'http://localhost:8000/api/v1';
};

export const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      clearAuthCookie();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================
// Auth
// ============================================================
export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    const { data } = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  },
  getMe: async (): Promise<User> => {
    const { data } = await api.get('/auth/me');
    return data;
  },
  register: async (payload: { email: string; password: string; full_name: string }): Promise<User> => {
    const { data } = await api.post('/auth/register', payload);
    return data;
  },
};

// ============================================================
// Dashboard
// ============================================================
export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const { data } = await api.get('/dashboard/stats');
    return data;
  },
  getCharts: async (): Promise<ChartData> => {
    const { data } = await api.get('/dashboard/charts');
    return data;
  },
  getRecentActivity: async (): Promise<RecentActivity[]> => {
    const { data } = await api.get('/dashboard/activity');
    return data;
  },
};

// ============================================================
// Jobs
// ============================================================
export const jobsApi = {
  getAll: async (params?: Record<string, string | number>): Promise<{ items: Job[]; total: number; page: number; pages: number }> => {
    const { data } = await api.get('/jobs', { params });
    return data;
  },
  getById: async (id: string): Promise<Job> => {
    const { data } = await api.get(`/jobs/${id}`);
    return data;
  },
  getMatch: async (jobId: string): Promise<JobMatch> => {
    const { data } = await api.get(`/jobs/${jobId}/match`);
    return data;
  },
};

// ============================================================
// Job Matches / Approval Queue
// ============================================================
export const matchesApi = {
  getPending: async (): Promise<JobMatch[]> => {
    const { data } = await api.get('/matches/pending');
    return data;
  },
  approve: async (matchId: string): Promise<JobMatch> => {
    const { data } = await api.post(`/matches/${matchId}/approve`);
    return data;
  },
  reject: async (matchId: string): Promise<JobMatch> => {
    const { data } = await api.post(`/matches/${matchId}/reject`);
    return data;
  },
  bulkApprove: async (matchIds: string[]): Promise<void> => {
    await api.post('/matches/bulk-approve', { match_ids: matchIds });
  },
};

// ============================================================
// Applications
// ============================================================
export const applicationsApi = {
  getAll: async (params?: Record<string, string | number>): Promise<{ items: Application[]; total: number; page: number; pages: number }> => {
    const { data } = await api.get('/applications', { params });
    return data;
  },
  getById: async (id: string): Promise<Application> => {
    const { data } = await api.get(`/applications/${id}`);
    return data;
  },
  updateStatus: async (id: string, status: string, notes?: string): Promise<Application> => {
    const { data } = await api.patch(`/applications/${id}/status`, { status, notes });
    return data;
  },
  addNote: async (id: string, note: string): Promise<Application> => {
    const { data } = await api.post(`/applications/${id}/notes`, { note });
    return data;
  },
};

// ============================================================
// Resume & Profile
// ============================================================
export const resumeApi = {
  upload: async (file: File): Promise<Resume> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  getAll: async (): Promise<Resume[]> => {
    const { data } = await api.get('/resumes');
    return data;
  },
  setPrimary: async (id: string): Promise<Resume> => {
    const { data } = await api.patch(`/resumes/${id}/primary`);
    return data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/resumes/${id}`);
  },
};

export const profileApi = {
  get: async (): Promise<CandidateProfile> => {
    const { data } = await api.get('/profile');
    return data;
  },
  update: async (profile: Partial<CandidateProfile>): Promise<CandidateProfile> => {
    const { data } = await api.put('/profile', profile);
    return data;
  },
  verify: async (): Promise<CandidateProfile> => {
    const { data } = await api.post('/profile/verify');
    return data;
  },
};

// ============================================================
// Preferences
// ============================================================
export const preferencesApi = {
  get: async (): Promise<Preference> => {
    const { data } = await api.get('/preferences');
    return data;
  },
  update: async (prefs: Partial<Preference>): Promise<Preference> => {
    const { data } = await api.put('/preferences', prefs);
    return data;
  },
};

// ============================================================
// Bot Controls
// ============================================================
export const botApi = {
  getSettings: async (): Promise<BotSettings> => {
    const { data } = await api.get('/bot/settings');
    return data;
  },
  updateSettings: async (settings: Partial<BotSettings>): Promise<BotSettings> => {
    const { data } = await api.put('/bot/settings', settings);
    return data;
  },
  start: async (): Promise<BotRun> => {
    const { data } = await api.post('/bot/start');
    return data;
  },
  pause: async (): Promise<void> => {
    await api.post('/bot/pause');
  },
  stop: async (): Promise<void> => {
    await api.post('/bot/stop');
  },
  getStatus: async (): Promise<{ status: 'running' | 'paused' | 'stopped' }> => {
    const { data } = await api.get('/bot/status');
    return data;
  },
  getRuns: async (): Promise<BotRun[]> => {
    const { data } = await api.get('/bot/runs');
    return data;
  },
  getRunLog: async (runId: string): Promise<string> => {
    const { data } = await api.get(`/bot/runs/${runId}/log`);
    return data;
  },
};

// ============================================================
// Notifications
// ============================================================
export const notificationsApi = {
  getAll: async (): Promise<Notification[]> => {
    const { data } = await api.get('/notifications');
    return data;
  },
  getUnreadCount: async (): Promise<number> => {
    const { data } = await api.get('/notifications/unread-count');
    return data.count;
  },
  markRead: async (id: string): Promise<void> => {
    await api.patch(`/notifications/${id}/read`);
  },
  markAllRead: async (): Promise<void> => {
    await api.post('/notifications/mark-all-read');
  },
};

// ============================================================
// Settings
// ============================================================
export const settingsApi = {
  getAccount: async (): Promise<User> => {
    const { data } = await api.get('/settings/account');
    return data;
  },
  updateAccount: async (payload: Partial<User & { password: string }>): Promise<User> => {
    const { data } = await api.put('/settings/account', payload);
    return data;
  },
  getNotificationPrefs: async (): Promise<Record<string, boolean>> => {
    const { data } = await api.get('/settings/notifications');
    return data;
  },
  updateNotificationPrefs: async (prefs: Record<string, boolean>): Promise<void> => {
    await api.put('/settings/notifications', prefs);
  },
  deleteAccount: async (): Promise<void> => {
    await api.delete('/settings/account');
  },
};

export default api;
