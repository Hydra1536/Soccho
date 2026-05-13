import { useState } from 'react';
import { Bell } from 'lucide-react';
import { Link } from 'react-router';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { Avatar } from '../components/Avatar';
import { BalanceChip } from '../components/BalanceChip';
import { NotificationDrawer } from '../components/NotificationDrawer';
import { BottomNav } from '../components/BottomNav';

const pieData = [
  { name: 'Given', value: 45000, color: '#4F46E5' },
  { name: 'Received', value: 30000, color: '#818CF8' }
];

const barData = [
  { month: 'Jan', amount: 5000 },
  { month: 'Feb', amount: 8000 },
  { month: 'Mar', amount: 6000 },
  { month: 'Apr', amount: 12000 },
  { month: 'May', amount: 9000 },
  { month: 'Jun', amount: 15000 }
];

const friends = [
  { id: 1, name: 'Rahim Khan', lastTransaction: 'Borrowed ৳5,000', balance: 5000, type: 'owed' as const },
  { id: 2, name: 'Fatima Ahmed', lastTransaction: 'Paid back ৳2,000', balance: -1500, type: 'owe' as const },
  { id: 3, name: 'Karim Hossain', lastTransaction: 'Borrowed ৳3,500', balance: 3500, type: 'owed' as const },
  { id: 4, name: 'Salma Begum', lastTransaction: 'Lent ৳4,000', balance: -4000, type: 'owe' as const }
];

const notifications = [
  {
    id: '1',
    type: 'pending' as const,
    title: 'Payment Confirmation Request',
    message: 'Rahim Khan claims he paid ৳2,000',
    timestamp: '5 minutes ago'
  },
  {
    id: '2',
    type: 'received' as const,
    title: 'Payment Received',
    message: 'Fatima Ahmed paid ৳2,000',
    timestamp: '2 hours ago'
  },
  {
    id: '3',
    type: 'reminder' as const,
    title: 'Payment Due',
    message: 'Salma Begum\'s payment is due tomorrow',
    timestamp: '1 day ago'
  }
];

export default function Home() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const notificationCount = notifications.filter(n => n.type === 'pending').length;

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      {/* Header */}
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center justify-between">
          <button
            onClick={() => setDrawerOpen(true)}
            className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <line x1="3" y1="6" x2="21" y2="6" strokeWidth="2" strokeLinecap="round"/>
              <line x1="3" y1="12" x2="21" y2="12" strokeWidth="2" strokeLinecap="round"/>
              <line x1="3" y1="18" x2="21" y2="18" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>

          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            Soccho
          </h1>

          <button
            onClick={() => setDrawerOpen(true)}
            className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors relative"
          >
            <Bell size={24} />
            {notificationCount > 0 && (
              <span className="absolute top-1 right-1 w-5 h-5 bg-[#EF4444] text-white text-xs rounded-full flex items-center justify-center font-medium">
                {notificationCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <NotificationDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        notifications={notifications}
      />

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Summary Charts */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="font-bold text-lg mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            Summary
          </h2>
          <div className="grid grid-cols-2 gap-4">
            {/* Pie Chart */}
            <div>
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={50}
                    paddingAngle={5}
                    dataKey="value"
                    animationDuration={800}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="text-center space-y-1 mt-2">
                <div className="flex items-center justify-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-[#4F46E5]" />
                  <span className="text-[#6B7280]">Given</span>
                </div>
                <div className="flex items-center justify-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-[#818CF8]" />
                  <span className="text-[#6B7280]">Received</span>
                </div>
              </div>
            </div>

            {/* Bar Chart */}
            <div>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart data={barData}>
                  <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                  <Bar dataKey="amount" fill="#4F46E5" radius={[4, 4, 0, 0]} animationDuration={800} />
                </BarChart>
              </ResponsiveContainer>
              <p className="text-center text-xs text-[#6B7280] mt-2">Monthly Trend</p>
            </div>
          </div>
        </div>

        {/* Friends List */}
        <div>
          <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Friends
          </h2>
          <div className="space-y-3">
            {friends.map((friend) => (
              <Link
                key={friend.id}
                to={`/friend/${friend.id}`}
                className="block"
              >
                <div className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-150">
                  <div className="flex items-center gap-3">
                    <Avatar name={friend.name} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{friend.name}</h3>
                      <p className="text-sm text-[#6B7280]">{friend.lastTransaction}</p>
                    </div>
                    <BalanceChip amount={Math.abs(friend.balance)} type={friend.type} />
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <button className="w-full mt-4 py-3 border-2 border-[#4F46E5] text-[#4F46E5] rounded-xl font-medium hover:bg-[#F3F4F6] transition-colors">
            Show More
          </button>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
