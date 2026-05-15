import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'https://soccho-gateway.onrender.com';

export const ACCESS_TOKEN_KEY = 'access_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';
export const USER_ID_KEY = 'user_id';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: false,
});

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  const userId = extractUserId(access);
  if (userId) {
    localStorage.setItem(USER_ID_KEY, userId);
  }
}

function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_ID_KEY);
}

function extractUserId(token: string): string | null {
  try {
    const [, payload] = token.split('.');
    if (!payload) {
      return null;
    }

    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
    const decoded = JSON.parse(atob(padded)) as { sub?: string };
    return decoded.sub || null;
  } catch {
    return null;
  }
}

function flushQueue(token: string | null): void {
  refreshQueue.forEach((resolve) => resolve(token));
  refreshQueue = [];
}

function redirectToLogin(): void {
  clearTokens();
  window.location.href = '/';
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const status = error.response?.status;

    if (!originalRequest || status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      redirectToLogin();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((token) => {
          if (!token) {
            reject(error);
            return;
          }
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(api(originalRequest));
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshResponse = await axios.post(
        `${API_URL}/api/auth/refresh/`,
        { refresh: refreshToken },
        { withCredentials: false }
      );

      const newAccess = refreshResponse.data?.access as string | undefined;
      const newRefresh = refreshResponse.data?.refresh as string | undefined;

      if (!newAccess || !newRefresh) {
        redirectToLogin();
        return Promise.reject(error);
      }

      setTokens(newAccess, newRefresh);
      flushQueue(newAccess);
      originalRequest.headers.Authorization = `Bearer ${newAccess}`;
      return api(originalRequest);
    } catch (refreshError) {
      flushQueue(null);
      redirectToLogin();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export function hasAccessToken(): boolean {
  return !!getAccessToken();
}

export function persistTokens(access: string, refresh: string): void {
  setTokens(access, refresh);
}

export function dropTokens(): void {
  clearTokens();
}

export default api;
