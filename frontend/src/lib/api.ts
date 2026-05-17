import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'https://soccho-gateway.onrender.com';
export const AUTH_SCHEME = (import.meta.env.VITE_AUTH_SCHEME || 'Bearer').trim() || 'Bearer';

export const ACCESS_TOKEN_KEY = 'access_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';
export const USER_ID_KEY = 'user_id';
export const USERNAME_KEY = 'username';
export const EMAIL_KEY = 'email';
const ACCESS_TOKEN_FALLBACK_KEYS = ['accessToken', 'token', 'jwt'] as const;
const REFRESH_TOKEN_FALLBACK_KEYS = ['refreshToken'] as const;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: false,
});

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

function normalizeStoredToken(raw: string | null): string | null {
  const trimmed = (raw || '').trim().replace(/^["']|["']$/g, '');
  if (!trimmed) {
    return null;
  }

  return trimmed.replace(/^(Bearer|JWT|Token)\s+/i, '').trim() || null;
}

export function getAccessToken(): string | null {
  const token = readStorageValue([ACCESS_TOKEN_KEY, ...ACCESS_TOKEN_FALLBACK_KEYS]);
  return normalizeStoredToken(token);
}

export function getRefreshToken(): string | null {
  const token = readStorageValue([REFRESH_TOKEN_KEY, ...REFRESH_TOKEN_FALLBACK_KEYS]);
  return normalizeStoredToken(token);
}

function readStorageValue(keys: readonly string[]): string | null {
  const storages: Storage[] = [localStorage, sessionStorage];
  for (const storage of storages) {
    for (const key of keys) {
      const value = storage.getItem(key);
      if (value && value.trim()) {
        return value;
      }
    }
  }
  return null;
}

function setTokens(access: string, refresh?: string): void {
  const normalizedAccess = normalizeStoredToken(access);
  const normalizedRefresh = normalizeStoredToken(typeof refresh === 'string' ? refresh : getRefreshToken());
  if (!normalizedAccess || !normalizedRefresh) {
    clearTokens();
    return;
  }

  localStorage.setItem(ACCESS_TOKEN_KEY, normalizedAccess);
  localStorage.setItem(REFRESH_TOKEN_KEY, normalizedRefresh);
  localStorage.removeItem(EMAIL_KEY);
  const userId = extractUserId(normalizedAccess);
  if (userId) {
    localStorage.setItem(USER_ID_KEY, userId);
  }
  const username = extractUsername(normalizedAccess);
  if (username) {
    localStorage.setItem(USERNAME_KEY, username);
  }
}

function clearTokens(): void {
  const storages: Storage[] = [localStorage, sessionStorage];
  for (const storage of storages) {
    storage.removeItem(ACCESS_TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
    storage.removeItem(USER_ID_KEY);
    storage.removeItem(USERNAME_KEY);
    storage.removeItem(EMAIL_KEY);
    ACCESS_TOKEN_FALLBACK_KEYS.forEach((key) => storage.removeItem(key));
    REFRESH_TOKEN_FALLBACK_KEYS.forEach((key) => storage.removeItem(key));
  }
}

function decodeTokenPayload(token: string): { sub?: string; exp?: number; username?: string } | null {
  try {
    const [, payload] = token.split('.');
    if (!payload) {
      return null;
    }

    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
    return JSON.parse(atob(padded)) as { sub?: string; exp?: number; username?: string };
  } catch {
    return null;
  }
}

function extractUserId(token: string): string | null {
  return decodeTokenPayload(token)?.sub || null;
}

function extractUsername(token: string): string | null {
  return decodeTokenPayload(token)?.username || null;
}

function flushQueue(token: string | null): void {
  refreshQueue.forEach((resolve) => resolve(token));
  refreshQueue = [];
}

function isPublicAuthEndpoint(url?: string): boolean {
  if (!url) {
    return false;
  }

  return [
    '/api/auth/login/',
    '/api/auth/register/',
    '/api/auth/otp/verify/',
    '/api/auth/forgot-password/',
    '/oauth/',
  ].some((endpoint) => url.includes(endpoint));
}

export function isTokenExpired(token: string, skewSeconds = 30): boolean {
  const exp = decodeTokenPayload(token)?.exp;
  if (!exp) {
    return true;
  }

  return Date.now() >= (exp - skewSeconds) * 1000;
}

export function redirectToLogin(): void {
  clearTokens();
  window.location.href = '/';
}

export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  if (isRefreshing) {
    return new Promise((resolve) => {
      refreshQueue.push(resolve);
    });
  }

  isRefreshing = true;

  try {
    const refreshResponse = await axios.post(
      `${API_URL}/api/auth/refresh/`,
      { refresh: refreshToken },
      { withCredentials: false }
    );

    const newAccess = refreshResponse.data?.access as string | undefined;
    const newRefresh = refreshResponse.data?.refresh as string | undefined;

    if (!newAccess) {
      flushQueue(null);
      return null;
    }

    setTokens(newAccess, newRefresh || refreshToken);
    flushQueue(newAccess);
    return newAccess;
  } catch {
    flushQueue(null);
    return null;
  } finally {
    isRefreshing = false;
  }
}

export async function getValidAccessToken(): Promise<string | null> {
  const token = getAccessToken();
  if (token && !isTokenExpired(token)) {
    return token;
  }

  if (!getRefreshToken()) {
    return null;
  }

  return refreshAccessToken();
}

export function buildAuthorizationHeader(token: string | null): string {
  const normalized = normalizeStoredToken(token);
  return normalized ? `${AUTH_SCHEME} ${normalized}` : '';
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (!isPublicAuthEndpoint(config.url)) {
    const authHeader = buildAuthorizationHeader(token);
    if (authHeader) {
      config.headers.Authorization = authHeader;
      config.headers.authorization = authHeader;
    }
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

    if (isPublicAuthEndpoint(originalRequest.url)) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      redirectToLogin();
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const newAccess = await refreshAccessToken();

      if (!newAccess) {
        redirectToLogin();
        return Promise.reject(error);
      }

      const authHeader = buildAuthorizationHeader(newAccess);
      originalRequest.headers.Authorization = authHeader;
      originalRequest.headers.authorization = authHeader;
      return api(originalRequest);
    } catch (refreshError) {
      redirectToLogin();
      return Promise.reject(refreshError);
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

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
  }
  return fallback;
}

export default api;
