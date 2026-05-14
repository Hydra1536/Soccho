import { useEffect, useMemo, useState } from 'react';
import { Bell } from 'lucide-react';
import { Link } from 'react-router';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, ResponsiveContainer } from 'recharts';
import api from '../../lib/api';
import { Avatar } from '../components/Avatar';
import { BalanceChip } from '../components/BalanceChip';
import { NotificationDrawer, type NotificationItem } from '../components/NotificationDrawer';
import { BottomNav } from '../components/BottomNav';

type DashboardSummary = {
  user_id: string;
  total_lent: number;
  total_borrowed: number;
  total_confirmed: number;
};

type FriendRow = {
  id: string;
  requester_id: string;
  addressee_id: string;
  status: string;
  created_at: string;
};

type FriendNode = {
  userId: string;
  username: string;
  loyaltyScore?: number | null;
};

type FriendCard = {
  id: string;
  name: string;
  lastTransaction: string;
  balance: number;
  type: 'owed' | 'owe';
};

export default function Home() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationCount, setNotificationCount] = useState(0);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [friendCards, setFriendCards] = useState<FriendCard[]>([]);

  useEffect(() => {
    const fetchDashboard = async () => {
      const userId = localStorage.getItem('user_id');
      if (!userId) return;

      const { data } = await api.post(
        '/graphql/',
        {
          query: `query DashboardSummary($userId: UUID!) { dashboardSummary(userId: $userId) { userId totalLent totalBorrowed totalConfirmed } }`,
          variables: { userId },
        },
        { headers: { 'X-Service': 'transaction' } }
      );
      if (data?.data?.dashboardSummary) {
        const row = data.data.dashboardSummary;
        setSummary({
          user_id: String(row.userId || userId),
          total_lent: Number(row.totalLent || 0),
          total_borrowed: Number(row.totalBorrowed || 0),
          total_confirmed: Number(row.totalConfirmed || 0),
        });
      }
    };

    const fetchFriends = async () => {
      const userId = localStorage.getItem('user_id');
      if (!userId) return;

      const [friendResponse, directoryResponse] = await Promise.all([
        api.get('/api/social/friends/'),
        api.post(
          '/graphql/',
          {
            query: `query FriendList { friendList { userId username loyaltyScore } }`,
          },
          { headers: { 'X-Service': 'social' } }
        ),
      ]);

      const rows: FriendRow[] = friendResponse.data?.results || friendResponse.data || [];
      const directory: FriendNode[] = directoryResponse.data?.data?.friendList || [];

      const cards = await Promise.all(
        rows.map(async (row, idx) => {
          const friendUserId = row.requester_id === userId ? row.addressee_id : row.requester_id;
          const friendMeta = directory.find((entry) => entry.userId === friendUserId);

          let netBalance = 0;
          try {
            const { data } = await api.post(
              '/graphql/',
              {
                query: `query FriendLedger($friendshipId: UUID!) { friendLedger(friendshipId: $friendshipId) { netBalance } }`,
                variables: { friendshipId: row.id },
              },
              { headers: { 'X-Service': 'transaction' } }
            );
            netBalance = Number(data?.data?.friendLedger?.netBalance || 0);
          } catch {
            netBalance = 0;
          }

          return {
            id: row.id,
            name: friendMeta?.username || `Friend ${idx + 1}`,
            lastTransaction: row.status,
            balance: Math.abs(netBalance),
            type: netBalance >= 0 ? 'owed' as const : 'owe' as const,
          };
        })
      );
      setFriendCards(cards);
    };

    void fetchDashboard();
    void fetchFriends();
  }, []);

  const pieData = useMemo(
    () => [
      { name: 'Given', value: Number(summary?.total_lent || 0), color: '#4F46E5' },
      { name: 'Received', value: Number(summary?.total_borrowed || 0), color: '#818CF8' },
    ],
    [summary]
  );

  const barData = useMemo(() => {
    const base = Number(summary?.total_confirmed || 0);
    return [
      { month: 'Jan', amount: base * 1 },
      { month: 'Feb', amount: base * 1.2 },
      { month: 'Mar', amount: base * 1.4 },
      { month: 'Apr', amount: base * 1.1 },
      { month: 'May', amount: base * 1.5 },
      { month: 'Jun', amount: base * 1.7 },
    ];
  }, [summary]);

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center justify-between">
          <button onClick={() => setDrawerOpen(true)} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <line x1="3" y1="6" x2="21" y2="6" strokeWidth="2" strokeLinecap="round" />
              <line x1="3" y1="12" x2="21" y2="12" strokeWidth="2" strokeLinecap="round" />
              <line x1="3" y1="18" x2="21" y2="18" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>

          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            Soccho
          </h1>

          <button onClick={() => setDrawerOpen(true)} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors relative">
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
        onNotificationsChange={setNotifications}
        onUnreadCountChange={setNotificationCount}
      />

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="font-bold text-lg mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            Summary
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={30} outerRadius={50} paddingAngle={5} dataKey="value" animationDuration={800}>
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>

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

        <div>
          <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Friends
          </h2>
          <div className="space-y-3">
            {friendCards.map((friend) => (
              <Link key={friend.id} to={`/friend/${friend.id}`} className="block">
                <div className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-150">
                  <div className="flex items-center gap-3">
                    <Avatar name={friend.name} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{friend.name}</h3>
                      <p className="text-sm text-[#6B7280]">{friend.lastTransaction}</p>
                    </div>
                    <BalanceChip amount={friend.balance} type={friend.type} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
