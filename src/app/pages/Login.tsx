import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { OTPInput } from '../components/OTPInput';

type AuthScreen = 'login' | 'register' | 'otp';

export default function Login() {
  const navigate = useNavigate();
  const [screen, setScreen] = useState<AuthScreen>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setScreen('otp');
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setScreen('otp');
  };

  const handleOTPComplete = (otp: string) => {
    console.log('OTP Verified:', otp);
    navigate('/home');
  };

  const handleGoogleAuth = () => {
    console.log('Google OAuth initiated');
    navigate('/home');
  };

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 300 : -300,
      opacity: 0
    }),
    center: {
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      x: direction > 0 ? -300 : 300,
      opacity: 0
    })
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
    <div className="min-h-screen w-full flex items-center justify-center p-4"
      style={{
        background: 'linear-gradient(150deg, #4F46E5 0%, #7C3AED 100%)'
      }}>

      <div className="w-full max-w-[360px]">
        <div className="bg-white rounded-[24px] p-8 shadow-2xl overflow-hidden">

          {/* Soccho Wordmark */}
          <h1 className="text-center text-3xl mb-8"
            style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: '#4F46E5' }}>
            Soccho
          </h1>

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
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  <Button type="submit" fullWidth className="mt-6">
                    Log In
                  </Button>

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
                    onClick={handleGoogleAuth}
                    className="flex items-center justify-center gap-3"
                  >
                    <svg width="18" height="18" viewBox="0 0 18 18">
                      <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
                      <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.183l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
                      <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707 0-.593.102-1.167.282-1.707V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.335z"/>
                      <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
                    </svg>
                    Google
                  </Button>

                  <p className="text-center text-sm text-[#6B7280] mt-6">
                    Don't have an account?{' '}
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
                    label="Full Name"
                    placeholder="John Doe"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
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
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />

                  <Button type="submit" fullWidth className="mt-6">
                    Create Account
                  </Button>

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
                    onClick={handleGoogleAuth}
                    className="flex items-center justify-center gap-3"
                  >
                    <svg width="18" height="18" viewBox="0 0 18 18">
                      <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
                      <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.183l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
                      <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707 0-.593.102-1.167.282-1.707V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.335z"/>
                      <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
                    </svg>
                    Google
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

                <OTPInput onComplete={handleOTPComplete} />

                <Button fullWidth onClick={() => navigate('/home')}>
                  Verify & Continue
                </Button>

                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => navigateTo('login')}
                    className="text-sm text-[#6B7280] hover:text-[#4F46E5]"
                  >
                    Didn't receive code? <span className="font-medium">Resend</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => navigateTo('login')}
                  className="w-full text-center text-sm text-[#6B7280] hover:text-[#111827]"
                >
                  ← Back to login
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
