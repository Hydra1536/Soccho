import api, { dropTokens, persistTokens } from './api';

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
  const refresh = localStorage.getItem('refresh_token');
  try {
    if (refresh) {
      await api.post('/api/auth/logout/', { refresh });
    }
  } finally {
    dropTokens();
  }
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential?: string }) => void;
            ux_mode?: 'popup' | 'redirect';
          }) => void;
          prompt: () => void;
        };
      };
    };
  }
}

function loadGoogleIdentityScript(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-google-identity="true"]') as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error('Failed to load Google script')), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = 'true';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google script'));
    document.head.appendChild(script);
  });
}

export async function googleLogin(): Promise<void> {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  if (!clientId) {
    throw new Error('Missing VITE_GOOGLE_CLIENT_ID');
  }

  await loadGoogleIdentityScript();

  const idToken = await new Promise<string>((resolve, reject) => {
    let settled = false;
    const timeout = window.setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      reject(new Error('Google sign-in timed out. Verify Google OAuth Authorized JavaScript origins for this domain.'));
    }, 15000);

    const resolveOnce = (credential: string) => {
      if (settled) {
        return;
      }
      settled = true;
      window.clearTimeout(timeout);
      resolve(credential);
    };

    const rejectOnce = (reason: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      window.clearTimeout(timeout);
      reject(reason);
    };

    if (!window.google?.accounts?.id) {
      rejectOnce(new Error('Google Identity SDK unavailable'));
      return;
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      ux_mode: 'popup',
      callback: (response) => {
        if (!response.credential) {
          rejectOnce(new Error('No Google credential received'));
          return;
        }
        resolveOnce(response.credential);
      },
    });
    window.google.accounts.id.prompt();
  });

  const { data } = await api.post<TokenPair>('/oauth/', { id_token: idToken });
  persistTokens(data.access, data.refresh);
}
