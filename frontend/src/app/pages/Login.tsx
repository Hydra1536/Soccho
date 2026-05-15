import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Link, useNavigate } from 'react-router';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { OTPInput } from '../components/OTPInput';
import { googleLogin, login, register, verifyOTP, OTPContext } from '../../lib/auth';
import { persistTokens } from '../../lib/api';

type AuthScreen = 'login' | 'register' | 'otp';

export default function Login() {
  const navigate = useNavigate();
  const [screen, setScreen] = useState<AuthScreen>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [username, setUsername] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [otpContext, setOtpContext] = useState<OTPContext>('register');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const hash = new URLSearchParams(window.location.hash.slice(1));
    const accessToken = hash.get('access_token');
    const refreshToken = hash.get('refresh_token');
    const googleError = hash.get('google_error');
    if (!accessToken && !refreshToken && !googleError) {
      return;
    }

    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);

    if (accessToken && refreshToken) {
      persistTokens(accessToken, refreshToken);
      navigate('/home', { replace: true });
      return;
    }

    if (googleError) {
      setError(googleError);
    }
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/home');
    } catch {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(username, email, password, confirmPassword);
      setOtpContext('register');
      navigateTo('otp');
    } catch {
      setError('Unable to register');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!otpCode) {
      setError('Please enter the OTP code');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await verifyOTP(email, otpCode, otpContext);
      navigate('/home');
    } catch {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    setError(null);
    setLoading(true);
    void googleLogin();
  };

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: number) => ({
      x: direction > 0 ? -300 : 300,
      opacity: 0,
    }),
  };

  const getDirection = (from: AuthScreen, to: AuthScreen) => {
    const order: AuthScreen[] = ['login', 'register', 'otp'];
    return order.indexOf(to) > order.indexOf(from) ? 1 : -1;
  };

  const [direction, setDirection] = useState(1);

  const navigateTo = (newScreen: AuthScreen) => {
    setDirection(getDirection(screen, newScreen));
    setScreen(newScreen);
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center p-4"
      style={{
        background: 'linear-gradient(150deg, #4F46E5 0%, #7C3AED 100%)',
      }}
    >
      <div className="w-full max-w-[360px]">
        <div className="bg-white rounded-[24px] p-8 shadow-2xl overflow-hidden">
          <h1
            className="text-center text-3xl mb-8"
            style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: '#4F46E5' }}
          >
            Soccho
          </h1>

          {error && <p className="text-sm text-[#EF4444] mb-4 text-center">{error}</p>}

          <AnimatePresence mode="wait" custom={direction}>
            {screen === 'login' && (
              <motion.div
                key="login"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >
                <form onSubmit={handleLogin} className="space-y-4">
                  <Input
                    type="email"
                    label="Email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />

                  <Input
                    type="password"
                    label="Password"
                    placeholder="********"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  <Button type="submit" fullWidth className="mt-6" disabled={loading}>
                    {loading ? 'Signing In...' : 'Log In'}
                  </Button>

                  <div className="text-center">
                    <Link to="/forgot-password" className="text-sm text-[#4F46E5] hover:underline">
                      Forgot password?
                    </Link>
                  </div>

                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-[#E5E7EB]"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-white text-[#6B7280]">or continue with</span>
                    </div>
                  </div>

                  <Button
                    type="button"
                    variant="secondary"
                    fullWidth
                    onClick={handleGoogleLogin}
                    disabled={loading}
                    className="flex items-center justify-center gap-3"
                  >
                    Google
                  </Button>

                  <p className="text-center text-sm text-[#6B7280] mt-6">
                    Don&apos;t have an account?{' '}
                    <button
                      type="button"
                      onClick={() => navigateTo('register')}
                      className="text-[#4F46E5] font-medium hover:underline"
                    >
                      Sign up
                    </button>
                  </p>
                </form>
              </motion.div>
            )}

            {screen === 'register' && (
              <motion.div
                key="register"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >
                <form onSubmit={handleRegister} className="space-y-4">
                  <Input
                    type="text"
                    label="Username"
                    placeholder="john_doe"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />

                  <Input
                    type="email"
                    label="Email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />

                  <Input
                    type="password"
                    label="Password"
                    placeholder="********"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  <Input
                    type="password"
                    label="Confirm Password"
                    placeholder="********"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />

                  <Button type="submit" fullWidth className="mt-6" disabled={loading}>
                    {loading ? 'Creating...' : 'Create Account'}
                  </Button>

                  <p className="text-center text-sm text-[#6B7280] mt-6">
                    Already have an account?{' '}
                    <button
                      type="button"
                      onClick={() => navigateTo('login')}
                      className="text-[#4F46E5] font-medium hover:underline"
                    >
                      Log in
                    </button>
                  </p>
                </form>
              </motion.div>
            )}

            {screen === 'otp' && (
              <motion.div
                key="otp"
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.2, ease: 'easeOut' }}
                className="space-y-6"
              >
                <div className="text-center">
                  <h2 className="text-xl mb-2" style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>
                    Verify Your Account
                  </h2>
                  <p className="text-sm text-[#6B7280]">
                    Enter the 6-digit code sent to<br />
                    <span className="font-medium text-[#111827]">{email || 'your email'}</span>
                  </p>
                </div>

                <OTPInput onComplete={setOtpCode} />

                <Button fullWidth onClick={handleVerify} disabled={loading}>
                  {loading ? 'Verifying...' : 'Verify & Continue'}
                </Button>

                <button
                  type="button"
                  onClick={() => navigateTo('login')}
                  className="w-full text-center text-sm text-[#6B7280] hover:text-[#111827]"
                >
                  Back to login
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
