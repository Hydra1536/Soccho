import { useEffect, useState } from 'react';
import { ArrowLeft, LogOut, Lock } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Avatar } from '../components/Avatar';
import { BottomNav } from '../components/BottomNav';
import { fetchCurrentUser, logout } from '../../lib/auth';
import api, { EMAIL_KEY, USERNAME_KEY, getApiErrorMessage } from '../../lib/api';

export default function Profile() {
  const navigate = useNavigate();
  const [userName, setUserName] = useState(localStorage.getItem(USERNAME_KEY) || '');
  const [userEmail, setUserEmail] = useState(localStorage.getItem(EMAIL_KEY) || '');
  const [profileError, setProfileError] = useState('');
  const [canChangePassword, setCanChangePassword] = useState(false);
  const [loyaltyScore, setLoyaltyScore] = useState<number | null>(null);

  useEffect(() => {
    let isMounted = true;

    const loadProfile = async () => {
      try {
        const profile = await fetchCurrentUser();
        if (!isMounted) {
          return;
        }

        setUserName(profile.username);
        setUserEmail(profile.email);
        setCanChangePassword(profile.has_password);
        setProfileError('');
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setProfileError(getApiErrorMessage(error, 'Unable to load profile details right now.'));
      }
    };

    const loadLoyaltyScore = async () => {
      try {
        const { data } = await api.get<{ loyalty_score?: number }>('/api/social/loyalty-score/');
        if (!isMounted) {
          return;
        }
        const raw = Number(data?.loyalty_score ?? 0);
        const bounded = Math.max(0, Math.min(100, Number.isFinite(raw) ? raw : 0));
        setLoyaltyScore(bounded);
      } catch {
        if (!isMounted) {
          return;
        }
        setLoyaltyScore(null);
      }
    };

    void loadProfile();
    void loadLoyaltyScore();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center gap-3">
          <button onClick={() => navigate('/home')} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors">
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            Profile
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
          <div className="flex justify-center mb-4">
            <Avatar name={userName || 'User'} size="large" />
          </div>
          <h2 className="font-bold text-xl mb-1" style={{ fontFamily: 'var(--font-display)' }}>
            {userName || 'Loading profile...'}
          </h2>
          <p className="text-sm text-[#6B7280]">{userEmail || 'Fetching your account details...'}</p>
          {loyaltyScore !== null && (
            <div className="mt-4">
              <p className="text-xs text-[#6B7280] mb-1">Loyalty Score</p>
              <div className="h-2 rounded-full bg-[#E5E7EB] overflow-hidden">
                <div className="h-full bg-[#4F46E5] rounded-full transition-all" style={{ width: `${loyaltyScore}%` }} />
              </div>
              <p className="text-sm text-[#111827] mt-2 font-medium">{loyaltyScore.toFixed(1)} / 100</p>
            </div>
          )}
          {profileError && <p className="mt-3 text-sm text-[#EF4444]">{profileError}</p>}
        </div>

        <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
          {canChangePassword && (
            <button
              className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB]"
              onClick={() => navigate('/change-password')}
            >
              <Lock size={20} className="text-[#6B7280]" />
              <span className="flex-1 text-left text-[#111827]">Change Password</span>
            </button>
          )}
          <button onClick={handleLogout} className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#FEE2E2] transition-colors">
            <LogOut size={20} className="text-[#EF4444]" />
            <span className="flex-1 text-left text-[#EF4444]">Log Out</span>
          </button>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
