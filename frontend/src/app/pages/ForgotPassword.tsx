import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { forgotPassword, verifyOTP } from '../../lib/auth';
import { OTPInput } from '../components/OTPInput';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await forgotPassword(email);
      setStep('otp');
    } catch {
      setError('Unable to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const submitOtp = async () => {
    setLoading(true);
    setError(null);
    try {
      await verifyOTP(username, otp, 'forgot');
      navigate('/home');
    } catch {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(160deg, #4F46E5 0%, #312E81 100%)' }}
    >
      <div className="w-full max-w-[360px] bg-white rounded-[24px] p-8 shadow-2xl">
        <button className="mb-4 p-2 rounded-lg hover:bg-[#F3F4F6]" onClick={() => navigate('/')}>
          <ArrowLeft size={20} />
        </button>

        <h1 className="text-2xl mb-2" style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>
          Forgot Password
        </h1>
        <p className="text-sm text-[#6B7280] mb-6">Recover access with a one-time verification code.</p>

        {error && <p className="text-sm text-[#EF4444] mb-3">{error}</p>}

        {step === 'email' ? (
          <form onSubmit={submitEmail} className="space-y-4">
            <Input
              type="email"
              label="Email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="text"
              label="Username"
              placeholder="your_username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Button fullWidth type="submit" disabled={loading}>
              {loading ? 'Sending...' : 'Send OTP'}
            </Button>
          </form>
        ) : (
          <div className="space-y-4">
            <OTPInput onComplete={setOtp} />
            <Button fullWidth onClick={submitOtp} disabled={loading}>
              {loading ? 'Verifying...' : 'Verify OTP'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
