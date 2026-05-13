import api, { dropTokens, persistTokens } from './api';

export type OTPContext = 'register' | 'forgot' | 'change_pw';

type TokenPair = {
  access: string;
  refresh: string;
};

export async function login(username: string, password: string): Promise<void> {
  const { data } = await api.post<TokenPair>('/api/auth/login/', { username, password });
  persistTokens(data.access, data.refresh);
}

export async function register(username: string, email: string, password: string, confirmPassword: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/api/auth/register/', {
    username,
    email,
    password,
    confirm_password: confirmPassword,
  });
  return data;
}

export async function verifyOTP(username: string, code: string, context: OTPContext): Promise<void> {
  const { data } = await api.post<TokenPair>('/api/auth/otp/verify/', {
    username,
    code,
    context,
  });
  persistTokens(data.access, data.refresh);
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/api/auth/forgot-password/', { email });
  return data;
}

export async function requestChangePassword(username: string, old_password: string, new_password: string, confirm_password: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/api/auth/change-password/request/', {
    username,
    old_password,
    new_password,
    confirm_password,
  });
  return data;
}

export async function logout(): Promise<void> {
  const refresh = localStorage.getItem('refresh_token');
  try {
    if (refresh) {
      await api.post('/api/auth/logout/', { refresh });
    }
  } finally {
    dropTokens();
  }
}

export function googleLogin(): void {
  const base = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  window.location.href = `${base}/oauth/`;
}
