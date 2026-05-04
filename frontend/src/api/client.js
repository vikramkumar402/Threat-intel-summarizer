import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

const TOKENS = {
  access: 'token',
  refresh: 'refresh_token',
};

export function saveTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(TOKENS.access, access_token);
  if (refresh_token) localStorage.setItem(TOKENS.refresh, refresh_token);
}

export function clearTokens() {
  localStorage.removeItem(TOKENS.access);
  localStorage.removeItem(TOKENS.refresh);
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKENS.access);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const refresh = localStorage.getItem(TOKENS.refresh);
    if (
      error.response?.status === 401 &&
      !original._retried &&
      refresh &&
      !original.url.includes('/auth/refresh')
    ) {
      original._retried = true;
      try {
        if (!refreshing) {
          refreshing = axios
            .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refresh })
            .then((r) => {
              saveTokens(r.data);
              return r.data.access_token;
            })
            .finally(() => {
              refreshing = null;
            });
        }
        const newToken = await refreshing;
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch (e) {
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  },
);

export const auth = {
  register: (email, password) => api.post('/auth/register', { email, password }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  refresh: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
  logout: () =>
    api.post('/auth/logout', { refresh_token: localStorage.getItem(TOKENS.refresh) || '' }),
  getMe: () => api.get('/auth/me'),
};

export const intel = {
  getItems: (params) => api.get('/intel/items', { params }),
  getItem: (id) => api.get(`/intel/items/${id}`),
  triggerScrape: () => api.post('/intel/scrape'),
  getJob: (id) => api.get(`/intel/jobs/${id}`),
  listJobs: () => api.get('/intel/jobs'),
  listSources: () => api.get('/intel/sources/list'),
  getStats: () => api.get('/intel/stats'),
};

export const briefs = {
  getLatest: () => api.get('/briefs/latest'),
  getByDate: (date) => api.get(`/briefs/${date}`),
  list: (params) => api.get('/briefs', { params }),
};

export const users = {
  updateDigestSettings: (settings) => api.put('/users/me/digest-settings', settings),
  previewDigest: () => api.get('/users/me/digest-preview'),
};

export const adminApi = {
  listUsers: () => api.get('/admin/users'),
  setRole: (id, role) => api.put(`/admin/users/${id}/role`, null, { params: { role } }),
  setActive: (id, isActive) =>
    api.put(`/admin/users/${id}/active`, null, { params: { is_active: isActive } }),
  listSources: () => api.get('/admin/sources'),
  setSourceEnabled: (source, enabled) =>
    api.put(`/admin/sources/${source}/enabled`, null, { params: { enabled } }),
};

export default api;
