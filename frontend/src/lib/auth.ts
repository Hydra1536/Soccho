import api, { API_URL, dropTokens, getRefreshToken, persistTokens } from './api';

export type OTPContext = 'register' | 'forgot' | 'change_pw';

type TokenPair = {
  access: string;
  refresh: string;
};

export async function login(email: string, password: string): Promise<void> {
  const { data } = await api.post<TokenPair>('/api/auth/login/', { email, password });
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

export async function verifyOTP(email: string, code: string, context: OTPContext): Promise<void> {
  const { data } = await api.post<TokenPair>('/api/auth/otp/verify/', {
    email,
    code,
    context,
  });
  persistTokens(data.access, data.refresh);
}

export async function forgotPassword(email: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/api/auth/forgot-password/', { email });
  return data;
}

export async function requestChangePassword(email: string, old_password: string, new_password: string, confirm_password: string): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/api/auth/change-password/request/', {
    email,
    old_password,
    new_password,
    confirm_password,
  });
  return data;
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  try {
    if (refresh) {
      await api.post('/api/auth/logout/', { refresh });
    }
  } finally {
    dropTokens();
  }
}

export async function googleLogin(): Promise<void> {
  const params = new URLSearchParams({
    frontend_origin: window.location.origin,
  });
  window.location.assign(`${API_URL}/oauth/google/start/?${params.toString()}`);
  return new Promise(() => undefined);
}
