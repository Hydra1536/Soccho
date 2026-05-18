import { useEffect, useMemo, useState } from 'react';
import { Bell, Calculator } from 'lucide-react';
import { Link } from 'react-router';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, ResponsiveContainer } from 'recharts';
import { useApolloClient, useQuery } from '@apollo/client';
import { GET_DASHBOARD_SUMMARY, GET_FRIEND_LEDGER } from '../../graphql/queries';
import api, { getAccessToken } from '../../lib/api';
import { toDeterministicFriendshipUuid } from '../../lib/friendshipKey';
import { Avatar } from '../components/Avatar';
import { BalanceChip } from '../components/BalanceChip';
import { EqualPayDrawer } from '../components/EqualPayDrawer';
import { NotificationDrawer, type NotificationItem } from '../components/NotificationDrawer';
import { BottomNav } from '../components/BottomNav';

type DashboardSummaryNode = {
  userId: string;
  totalLent: number;
  totalBorrowed: number;
  totalConfirmed: number;
  loyaltyScore?: number;
  monthlyTrend?: Array<{
    monthKey: string;
    label: string;
    given: number;
    received: number;
  }>;
};

type FriendApiRow = {
  id: string;
  requester_id: string;
  addressee_id: string;
  status: string;
  created_at: string;
  counterpart_id: string;
  counterpart_username: string;
};

type FriendCard = {
  id: string;
  name: string;
  subtitle: string;
  balance: number;
  type: 'owed' | 'owe';
  pendingTotal: number;
};

export default function Home() {
  const apolloClient = useApolloClient();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [equalPayOpen, setEqualPayOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationCount, setNotificationCount] = useState(0);
  const [friendCards, setFriendCards] = useState<FriendCard[]>([]);
  const [friendsLoading, setFriendsLoading] = useState(false);
  const [friendsLoadingMore, setFriendsLoadingMore] = useState(false);
  const [nextFriendsCursor, setNextFriendsCursor] = useState<string | null>(null);
  const [friendsErrorMessage, setFriendsErrorMessage] = useState('');

  const resolvedUserId = useMemo(() => {
    const local = (localStorage.getItem('user_id') || '').trim();
    if (local) {
      return local;
    }
    const token = getAccessToken();
    if (!token) {
      return '';
    }
    try {
      const [, payload] = token.split('.');
      if (!payload) {
        return '';
      }
      const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
      const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=');
      const parsed = JSON.parse(atob(padded)) as { sub?: string };
      return String(parsed?.sub || '').trim();
    } catch {
      return '';
    }
  }, []);

  const {
    data: summaryData,
    previousData: previousSummaryData,
    loading: summaryLoading,
    error: summaryError,
  } = useQuery<{ dashboardSummary: DashboardSummaryNode }>(GET_DASHBOARD_SUMMARY, {
    variables: { userId: resolvedUserId },
    skip: !resolvedUserId,
    context: { service: 'transaction' },
    errorPolicy: 'all',
    returnPartialData: true,
    notifyOnNetworkStatusChange: true,
  });

  const summary = summaryData?.dashboardSummary || previousSummaryData?.dashboardSummary || null;
  const isOffline = typeof navigator !== 'undefined' ? !navigator.onLine : false;

  useEffect(() => {
    let cancelled = false;

    const extractCursor = (nextUrl: string | null): string | null => {
      if (!nextUrl) {
        return null;
      }
      try {
        const parsed = nextUrl.startsWith('http') ? new URL(nextUrl) : new URL(nextUrl, window.location.origin);
        return parsed.searchParams.get('cursor');
      } catch {
        return null;
      }
    };

    const buildCard = async (friend: FriendApiRow, idx: number): Promise<FriendCard> => {
      let netBalance = 0;
      let pendingReceivable = 0;
      let pendingPayable = 0;

      try {
        const { data } = await apolloClient.query({
          query: GET_FRIEND_LEDGER,
          variables: { friendshipId: toDeterministicFriendshipUuid(String(friend.id || '')) },
          context: { service: 'transaction' },
          fetchPolicy: 'network-only',
        });
        netBalance = Number(data?.friendLedger?.netBalance || 0);
        pendingReceivable = Number(data?.friendLedger?.pendingReceivable || 0);
        pendingPayable = Number(data?.friendLedger?.pendingPayable || 0);
      } catch {
        const cached = apolloClient.readQuery({
          query: GET_FRIEND_LEDGER,
          variables: { friendshipId: toDeterministicFriendshipUuid(String(friend.id || '')) },
        }) as { friendLedger?: { netBalance?: number; pendingReceivable?: number; pendingPayable?: number } } | null;
        netBalance = Number(cached?.friendLedger?.netBalance || 0);
        pendingReceivable = Number(cached?.friendLedger?.pendingReceivable || 0);
        pendingPayable = Number(cached?.friendLedger?.pendingPayable || 0);
      }

      const pendingTotal = Math.abs(pendingReceivable) + Math.abs(pendingPayable);
      const pendingNet = pendingReceivable - pendingPayable;
      let subtitle = 'কোনো বকেয়া নেই';
      if (pendingNet > 0) {
        subtitle = `আপনি পাবেন ${Math.abs(pendingNet).toLocaleString()} টাকা`;
      } else if (pendingNet < 0) {
        subtitle = `আপনাকে দিতে হবে ${Math.abs(pendingNet).toLocaleString()} টাকা`;
      } else if (netBalance > 0) {
        subtitle = `আপনি পাবেন ${Math.abs(netBalance).toLocaleString()} টাকা`;
      } else if (netBalance < 0) {
        subtitle = `আপনাকে দিতে হবে ${Math.abs(netBalance).toLocaleString()} টাকা`;
      }

      return {
        id: String(friend.id || ''),
        name: friend.counterpart_username || `Friend ${idx + 1}`,
        subtitle,
        balance: Math.abs(netBalance),
        type: netBalance >= 0 ? ('owed' as const) : ('owe' as const),
        pendingTotal,
      };
    };

    const sortCards = (rows: FriendCard[]) =>
      [...rows].sort((a, b) => {
        if (b.pendingTotal !== a.pendingTotal) {
          return b.pendingTotal - a.pendingTotal;
        }
        if (b.balance !== a.balance) {
          return b.balance - a.balance;
        }
        return a.name.localeCompare(b.name);
      });

    const fetchFriendPage = async (cursor: string | null, append: boolean) => {
      if (!resolvedUserId) {
        return;
      }
      if (append) {
        setFriendsLoadingMore(true);
      } else {
        setFriendsLoading(true);
      }
      setFriendsErrorMessage('');

      try {
        const params = cursor ? { cursor } : {};
        const { data } = await api.get('/api/social/list/', { params });
        const rows = Array.isArray(data?.results) ? (data.results as FriendApiRow[]) : [];
        const built = await Promise.all(rows.map((row, idx) => buildCard(row, idx)));
        if (cancelled) {
          return;
        }
        setFriendCards((prev) => {
          if (!append) {
            return sortCards(built);
          }
          const byId = new Map<string, FriendCard>();
          prev.forEach((item) => byId.set(item.id, item));
          built.forEach((item) => byId.set(item.id, item));
          return sortCards(Array.from(byId.values()));
        });
        setNextFriendsCursor(extractCursor(data?.next || null));
      } catch {
        if (!cancelled && !append) {
          setFriendCards([]);
        }
        if (!cancelled) {
          setFriendsErrorMessage('এই মুহূর্তে বন্ধুদের তথ্য লোড করা যাচ্ছে না।');
          setNextFriendsCursor(null);
        }
      } finally {
        if (!cancelled) {
          if (append) {
            setFriendsLoadingMore(false);
          } else {
            setFriendsLoading(false);
          }
        }
      }
    };

    void fetchFriendPage(null, false);
    return () => {
      cancelled = true;
    };
  }, [apolloClient, resolvedUserId]);

  const handleLoadMoreFriends = async () => {
    if (!nextFriendsCursor || friendsLoadingMore) {
      return;
    }

    setFriendsLoadingMore(true);
    try {
      const { data } = await api.get('/api/social/list/', { params: { cursor: nextFriendsCursor } });
      const rows = Array.isArray(data?.results) ? (data.results as FriendApiRow[]) : [];
      const built = await Promise.all(
        rows.map(async (friend, idx) => {
          let netBalance = 0;
          let pendingReceivable = 0;
          let pendingPayable = 0;

          try {
            const { data: ledgerData } = await apolloClient.query({
              query: GET_FRIEND_LEDGER,
              variables: { friendshipId: toDeterministicFriendshipUuid(String(friend.id || '')) },
              context: { service: 'transaction' },
              fetchPolicy: 'network-only',
            });
            netBalance = Number(ledgerData?.friendLedger?.netBalance || 0);
            pendingReceivable = Number(ledgerData?.friendLedger?.pendingReceivable || 0);
            pendingPayable = Number(ledgerData?.friendLedger?.pendingPayable || 0);
          } catch {
            const cached = apolloClient.readQuery({
              query: GET_FRIEND_LEDGER,
              variables: { friendshipId: toDeterministicFriendshipUuid(String(friend.id || '')) },
            }) as { friendLedger?: { netBalance?: number; pendingReceivable?: number; pendingPayable?: number } } | null;
            netBalance = Number(cached?.friendLedger?.netBalance || 0);
            pendingReceivable = Number(cached?.friendLedger?.pendingReceivable || 0);
            pendingPayable = Number(cached?.friendLedger?.pendingPayable || 0);
          }

          const pendingTotal = Math.abs(pendingReceivable) + Math.abs(pendingPayable);
          const pendingNet = pendingReceivable - pendingPayable;
          let subtitle = 'কোনো বকেয়া নেই';
          if (pendingNet > 0) {
            subtitle = `আপনি পাবেন ${Math.abs(pendingNet).toLocaleString()} টাকা`;
          } else if (pendingNet < 0) {
            subtitle = `আপনাকে দিতে হবে ${Math.abs(pendingNet).toLocaleString()} টাকা`;
          } else if (netBalance > 0) {
            subtitle = `আপনি পাবেন ${Math.abs(netBalance).toLocaleString()} টাকা`;
          } else if (netBalance < 0) {
            subtitle = `আপনাকে দিতে হবে ${Math.abs(netBalance).toLocaleString()} টাকা`;
          }

          return {
            id: String(friend.id || ''),
            name: friend.counterpart_username || `Friend ${idx + 1}`,
            subtitle,
            balance: Math.abs(netBalance),
            type: netBalance >= 0 ? ('owed' as const) : ('owe' as const),
            pendingTotal,
          } satisfies FriendCard;
        })
      );

      setFriendCards((prev) => {
        const byId = new Map<string, FriendCard>();
        prev.forEach((item) => byId.set(item.id, item));
        built.forEach((item) => byId.set(item.id, item));
        return Array.from(byId.values()).sort((a, b) => {
          if (b.pendingTotal !== a.pendingTotal) {
            return b.pendingTotal - a.pendingTotal;
          }
          if (b.balance !== a.balance) {
            return b.balance - a.balance;
          }
          return a.name.localeCompare(b.name);
        });
      });
      const nextUrl = data?.next || null;
      if (!nextUrl) {
        setNextFriendsCursor(null);
      } else {
        try {
          const parsed = nextUrl.startsWith('http') ? new URL(nextUrl) : new URL(nextUrl, window.location.origin);
          setNextFriendsCursor(parsed.searchParams.get('cursor'));
        } catch {
          setNextFriendsCursor(null);
        }
      }
    } catch {
      setFriendsErrorMessage('আরও বন্ধু লোড করা যাচ্ছে না।');
    } finally {
      setFriendsLoadingMore(false);
    }
  };

  const pieData = useMemo(
    () => [
      { name: 'Given', value: Number(summary?.totalLent || 0), color: '#4F46E5' },
      { name: 'Received', value: Number(summary?.totalBorrowed || 0), color: '#818CF8' },
    ],
    [summary]
  );

  const barData = useMemo(() => {
    const rows = summary?.monthlyTrend || [];
    if (!rows.length) {
      return [];
    }
    return rows.map((row) => ({
      month: row.label,
      given: Number(row.given || 0),
      received: Number(row.received || 0),
    }));
  }, [summary]);

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center justify-between">
          <button onClick={() => setEqualPayOpen(true)} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors" aria-label="Open EqualPay Calculator">
            <Calculator size={24} />
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
      <EqualPayDrawer isOpen={equalPayOpen} onClose={() => setEqualPayOpen(false)} />

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h2 className="font-bold text-lg mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            Summary
          </h2>
          {summaryLoading && !summary && <p className="text-sm text-[#6B7280] mb-4">Loading summary...</p>}
          {summaryError && !summary && <p className="text-sm text-[#B45309] mb-4">Unable to load summary right now.</p>}
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
              {barData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={150}>
                    <BarChart data={barData}>
                      <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                      <Bar dataKey="given" fill="#4F46E5" radius={[4, 4, 0, 0]} animationDuration={800} />
                      <Bar dataKey="received" fill="#818CF8" radius={[4, 4, 0, 0]} animationDuration={800} />
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-center text-xs text-[#6B7280] mt-2">Monthly Trend</p>
                  <p className="text-center text-[11px] text-[#6B7280] mt-1">Given vs Received</p>
                </>
              ) : (
                <div className="h-[150px] rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] flex items-center justify-center">
                  <p className="text-xs text-[#6B7280]">No monthly transaction data yet.</p>
                </div>
              )}
            </div>
          </div>
          <div className="mt-3 rounded-lg bg-[#EEF2FF] border border-[#C7D2FE] p-3">
            <p className="text-xs text-[#3730A3]">Loyalty Score</p>
            <p className="text-lg font-semibold text-[#1E1B4B]">{Number(summary?.loyaltyScore || 0).toFixed(1)} / 100</p>
          </div>
          <div className="grid grid-cols-3 gap-2 mt-4">
            <div className="rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] p-3 text-center">
              <p className="text-xs text-[#6B7280]">Given</p>
              <p className="text-sm font-semibold text-[#111827]">TK {Number(summary?.totalLent || 0).toLocaleString()}</p>
            </div>
            <div className="rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] p-3 text-center">
              <p className="text-xs text-[#6B7280]">Received</p>
              <p className="text-sm font-semibold text-[#111827]">TK {Number(summary?.totalBorrowed || 0).toLocaleString()}</p>
            </div>
            <div className="rounded-lg bg-[#F9FAFB] border border-[#E5E7EB] p-3 text-center">
              <p className="text-xs text-[#6B7280]">Confirmed</p>
              <p className="text-sm font-semibold text-[#111827]">{Number(summary?.totalConfirmed || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div>
          <h2 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            বন্ধুদের হিসাব
          </h2>
          {friendsLoading && friendCards.length === 0 && <p className="text-sm text-[#6B7280] mb-3">বন্ধুদের তথ্য লোড হচ্ছে...</p>}
          {friendsErrorMessage && <p className="text-sm text-[#B45309] mb-3">{friendsErrorMessage}</p>}
          {isOffline && friendCards.length > 0 && <p className="text-xs text-[#6B7280] mb-3">অফলাইন মোড: সেভ করা ডেটা দেখানো হচ্ছে।</p>}
          <div className="space-y-3">
            {friendCards.map((friend) => (
              <Link key={friend.id} to={`/friend/${friend.id}`} className="block">
                <div className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-150">
                  <div className="flex items-center gap-3">
                    <Avatar name={friend.name} size="medium" />
                    <div className="flex-1">
                      <h3 className="font-medium text-[#111827]">{friend.name}</h3>
                      <p className="text-sm text-[#6B7280]">{friend.subtitle}</p>
                    </div>
                    <BalanceChip amount={friend.balance} type={friend.type} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
          {!!nextFriendsCursor && (
            <button
              onClick={() => void handleLoadMoreFriends()}
              disabled={friendsLoadingMore}
              className={`mt-3 w-full h-10 rounded-xl text-sm font-medium transition-colors ${
                friendsLoadingMore ? 'bg-[#E5E7EB] text-[#6B7280]' : 'bg-[#111827] text-white hover:bg-black'
              }`}
            >
              {friendsLoadingMore ? 'লোড হচ্ছে...' : 'আরও ৫ জন দেখুন'}
            </button>
          )}
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
