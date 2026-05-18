import api, { API_URL, EMAIL_KEY, USERNAME_KEY, dropTokens, getRefreshToken, persistTokens } from './api';

export type OTPContext = 'register' | 'forgot' | 'change_pw';

type TokenPair = {
  access: string;
  refresh: string;
};

export type CurrentUser = {
  id: string;
  username: string;
  email: string;
  is_verified: boolean;
  has_password: boolean;
};

type WarmupStatusCallback = (statusMessage: string) => void;

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

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
      try {
        await api.post('/api/auth/logout/', { refresh });
      } catch {
        // A revoked or already-rotated refresh token should not block local sign-out.
      }
    }
  } finally {
    dropTokens();
  }
}

export async function googleLogin(onWarmupStatus?: WarmupStatusCallback): Promise<void> {
  const attempts = 3;
  const params = new URLSearchParams({ frontend_origin: window.location.origin });
  const oauthStartUrl = `${API_URL}/oauth/google/start/?${params.toString()}`;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    onWarmupStatus?.(`Waking backend services... (${attempt}/${attempts})`);
    try {
      await api.get('/healthz', { timeout: 20000 });
      await api.get('/api/auth/health/', { timeout: 45000 });
      window.location.assign(oauthStartUrl);
      return new Promise(() => undefined);
    } catch {
      if (attempt < attempts) {
        await wait(1200 * attempt);
      }
    }
  }

  throw new Error('Services are still waking up. Please try Google sign-in again in a few seconds.');
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const maxAttempts = 3;
  let lastError: unknown = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      const { data } = await api.get<CurrentUser>('/api/auth/me/');
      localStorage.setItem(USERNAME_KEY, data.username);
      localStorage.setItem(EMAIL_KEY, data.email);
      return data;
    } catch (error: any) {
      lastError = error;
      const status = Number(error?.response?.status || 0);
      const retryable = status === 502 || status === 503 || status === 504;
      if (!retryable || attempt === maxAttempts) {
        break;
      }
      await wait(900 * attempt);
    }
  }

  throw lastError;
}
