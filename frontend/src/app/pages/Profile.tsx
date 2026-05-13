import { ArrowLeft, Settings, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Avatar } from '../components/Avatar';
import { Button } from '../components/Button';
import { BottomNav } from '../components/BottomNav';

export default function Profile() {
  const navigate = useNavigate();
  const userName = 'Your Name';
  const userEmail = 'you@example.com';

  const handleLogout = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      {/* Header */}
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center gap-3">
          <button
            onClick={() => navigate('/home')}
            className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            Profile
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Profile Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
          <div className="flex justify-center mb-4">
            <Avatar name={userName} size="large" />
          </div>
          <h2 className="font-bold text-xl mb-1" style={{ fontFamily: 'var(--font-display)' }}>
            {userName}
          </h2>
          <p className="text-sm text-[#6B7280]">{userEmail}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-[#4F46E5]" style={{ fontFamily: 'var(--font-mono)' }}>
              12
            </p>
            <p className="text-xs text-[#6B7280] mt-1">Friends</p>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-[#10B981]" style={{ fontFamily: 'var(--font-mono)' }}>
              45K
            </p>
            <p className="text-xs text-[#6B7280] mt-1">Given</p>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
            <p className="text-2xl font-bold text-[#EF4444]" style={{ fontFamily: 'var(--font-mono)' }}>
              30K
            </p>
            <p className="text-xs text-[#6B7280] mt-1">Received</p>
          </div>
        </div>

        {/* Settings Options */}
        <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
          <button className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB]">
            <Settings size={20} className="text-[#6B7280]" />
            <span className="flex-1 text-left text-[#111827]">Settings</span>
          </button>
          <button
            onClick={handleLogout}
            className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#FEE2E2] transition-colors"
          >
            <LogOut size={20} className="text-[#EF4444]" />
            <span className="flex-1 text-left text-[#EF4444]">Log Out</span>
          </button>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
