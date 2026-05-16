import { useEffect, useMemo, useState } from 'react';
import { Bell } from 'lucide-react';
import { Link } from 'react-router';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, ResponsiveContainer } from 'recharts';
import { useApolloClient, useQuery } from '@apollo/client';
import { GET_DASHBOARD_SUMMARY, GET_FRIEND_LEDGER, GET_FRIENDS } from '../../graphql/queries';
import { Avatar } from '../components/Avatar';
import { BalanceChip } from '../components/BalanceChip';
import { NotificationDrawer, type NotificationItem } from '../components/NotificationDrawer';
import { BottomNav } from '../components/BottomNav';

type DashboardSummaryNode = {
  userId: string;
  totalLent: number;
  totalBorrowed: number;
  totalConfirmed: number;
};

type FriendNode = {
  friendshipId: string;
  requesterId: string;
  addresseeId: string;
  status: string;
  createdAt: string;
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
  const apolloClient = useApolloClient();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationCount, setNotificationCount] = useState(0);
  const [friendCards, setFriendCards] = useState<FriendCard[]>([]);
  const [friendsErrorMessage, setFriendsErrorMessage] = useState('');

  const userId = localStorage.getItem('user_id') || '';

  const {
    data: summaryData,
    previousData: previousSummaryData,
    loading: summaryLoading,
  } = useQuery<{ dashboardSummary: DashboardSummaryNode }>(GET_DASHBOARD_SUMMARY, {
    variables: { userId },
    skip: !userId,
    context: { service: 'transaction' },
  });

  const {
    data: friendsData,
    previousData: previousFriendsData,
    loading: friendsLoading,
    error: friendsError,
  } = useQuery<{ friendList: FriendNode[] }>(GET_FRIENDS, {
    skip: !userId,
    context: { service: 'social' },
  });

  const summary = summaryData?.dashboardSummary || previousSummaryData?.dashboardSummary || null;
  const friends = friendsData?.friendList || previousFriendsData?.friendList || [];
  const isOffline = typeof navigator !== 'undefined' ? !navigator.onLine : false;

  useEffect(() => {
    let cancelled = false;

    const buildFriendCards = async () => {
      if (!friends.length) {
        setFriendCards([]);
        setFriendsErrorMessage(friendsError ? 'Unable to load friends right now.' : '');
        return;
      }

      const cards = await Promise.all(
        friends.map(async (friend, idx) => {
          let netBalance = 0;

          try {
            const { data } = await apolloClient.query({
              query: GET_FRIEND_LEDGER,
              variables: { friendshipId: friend.friendshipId },
              context: { service: 'transaction' },
              fetchPolicy: 'network-only',
            });
            netBalance = Number(data?.friendLedger?.netBalance || 0);
          } catch {
            const cached = apolloClient.readQuery({
              query: GET_FRIEND_LEDGER,
              variables: { friendshipId: friend.friendshipId },
            }) as { friendLedger?: { netBalance?: number } } | null;
            netBalance = Number(cached?.friendLedger?.netBalance || 0);
          }

          return {
            id: friend.friendshipId,
            name: friend.username || `Friend ${idx + 1}`,
            lastTransaction: friend.status,
            balance: Math.abs(netBalance),
            type: netBalance >= 0 ? ('owed' as const) : ('owe' as const),
          };
        })
      );

      if (!cancelled) {
        setFriendCards(cards);
        setFriendsErrorMessage(friendsError ? 'Showing cached friends data.' : '');
      }
    };

    void buildFriendCards();
    return () => {
      cancelled = true;
    };
  }, [apolloClient, friends, friendsError]);

  const pieData = useMemo(
    () => [
      { name: 'Given', value: Number(summary?.totalLent || 0), color: '#4F46E5' },
      { name: 'Received', value: Number(summary?.totalBorrowed || 0), color: '#818CF8' },
    ],
    [summary]
  );

  const barData = useMemo(() => {
    const base = Number(summary?.totalConfirmed || 0);
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
          {summaryLoading && !summary && <p className="text-sm text-[#6B7280] mb-4">Loading summary...</p>}
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
          {friendsLoading && friendCards.length === 0 && <p className="text-sm text-[#6B7280] mb-3">Loading friends...</p>}
          {friendsErrorMessage && <p className="text-sm text-[#B45309] mb-3">{friendsErrorMessage}</p>}
          {isOffline && friendCards.length > 0 && <p className="text-xs text-[#6B7280] mb-3">Offline mode: showing cached data.</p>}
          {friendsError && friendCards.length === 0 && <p className="text-sm text-[#DC2626] mb-3">Unable to load friends right now.</p>}
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
