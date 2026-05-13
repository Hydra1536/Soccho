import { ArrowLeft, Settings, LogOut, Lock } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Avatar } from '../components/Avatar';
import { BottomNav } from '../components/BottomNav';
import { logout } from '../../lib/auth';

export default function Profile() {
  const navigate = useNavigate();
  const userName = localStorage.getItem('username') || 'Your Name';
  const userEmail = localStorage.getItem('email') || 'you@example.com';

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
            <Avatar name={userName} size="large" />
          </div>
          <h2 className="font-bold text-xl mb-1" style={{ fontFamily: 'var(--font-display)' }}>
            {userName}
          </h2>
          <p className="text-sm text-[#6B7280]">{userEmail}</p>
        </div>

        <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
          <button className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB]">
            <Settings size={20} className="text-[#6B7280]" />
            <span className="flex-1 text-left text-[#111827]">Settings</span>
          </button>
          <button
            className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB]"
            onClick={() => navigate('/change-password')}
          >
            <Lock size={20} className="text-[#6B7280]" />
            <span className="flex-1 text-left text-[#111827]">Change Password</span>
          </button>
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
