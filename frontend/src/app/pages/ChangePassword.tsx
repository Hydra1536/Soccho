import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { OTPInput } from '../components/OTPInput';
import { requestChangePassword, verifyOTP } from '../../lib/auth';
import { getApiErrorMessage } from '../../lib/api';

export default function ChangePassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState<'request' | 'otp'>('request');
  const [email, setEmail] = useState('');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await requestChangePassword(email, oldPassword, newPassword, confirmPassword);
      setStep('otp');
    } catch (error) {
      setError(getApiErrorMessage(error, 'Unable to request password change'));
    } finally {
      setLoading(false);
    }
  };

  const submitOtp = async () => {
    setLoading(true);
    setError(null);
    try {
      await verifyOTP(email, otp, 'change_pw');
      navigate('/home');
    } catch (error) {
      setError(getApiErrorMessage(error, 'Invalid credentials'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center p-4"
      style={{ background: 'radial-gradient(circle at top, #6366F1 0%, #312E81 70%)' }}
    >
      <div className="w-full max-w-[360px] bg-white rounded-[24px] p-8 shadow-2xl">
        <button className="mb-4 p-2 rounded-lg hover:bg-[#F3F4F6]" onClick={() => navigate('/profile')}>
          <ArrowLeft size={20} />
        </button>

        <h1 className="text-2xl mb-2" style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>
          Change Password
        </h1>
        <p className="text-sm text-[#6B7280] mb-6">Confirm with OTP to secure your account.</p>

        {error && <p className="text-sm text-[#EF4444] mb-3">{error}</p>}

        {step === 'request' ? (
          <form onSubmit={submitRequest} className="space-y-4">
            <Input type="email" label="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input type="password" label="Current Password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
            <Input type="password" label="New Password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
            <Input type="password" label="Confirm New Password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
            <Button fullWidth type="submit" disabled={loading}>
              {loading ? 'Requesting...' : 'Request OTP'}
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
