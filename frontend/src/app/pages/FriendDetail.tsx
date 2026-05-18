import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, ArrowUp, ArrowDown } from 'lucide-react';
import { useParams, useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { useQuery } from '@apollo/client';
import api from '../../lib/api';
import { toDeterministicFriendshipUuid } from '../../lib/friendshipKey';
import { GET_FRIEND_LEDGER, GET_FRIENDS } from '../../graphql/queries';
import { Avatar } from '../components/Avatar';
import { StatusChip } from '../components/StatusChip';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { BottomNav } from '../components/BottomNav';

type LedgerTx = {
  id: string;
  lender_id: string;
  borrower_id: string;
  friendship_id: string;
  amount: number;
  status: 'pending' | 'confirmed' | 'denied';
  due_date: string;
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

type LedgerNode = {
  friendshipId: string;
  netBalance: number;
  pendingReceivable?: number;
  pendingPayable?: number;
  transactions: Array<{
    id: string;
    lenderId: string;
    borrowerId: string;
    friendshipId: string;
    amount: number;
    status: 'pending' | 'confirmed' | 'denied';
    dueDate: string;
  }>;
};

export default function FriendDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [unfriendLoading, setUnfriendLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const myId = localStorage.getItem('user_id') || '';
  const ledgerFriendshipId = toDeterministicFriendshipUuid(String(id || ''));

  const {
    data: friendsData,
    previousData: previousFriendsData,
    loading: friendsLoading,
    error: friendsError,
  } = useQuery<{ friendList: FriendNode[] }>(GET_FRIENDS, {
    skip: !myId,
    context: { service: 'social' },
  });

  const {
    data: ledgerData,
    previousData: previousLedgerData,
    loading: ledgerLoading,
    error: ledgerError,
  } = useQuery<{ friendLedger: LedgerNode }>(GET_FRIEND_LEDGER, {
    variables: { friendshipId: ledgerFriendshipId },
    skip: !id,
    context: { service: 'transaction' },
  });

  const friends = friendsData?.friendList || previousFriendsData?.friendList || [];
  const friend = useMemo(() => friends.find((row) => String(row.friendshipId) === String(id)), [friends, id]);
  const friendUserId = friend?.requesterId === myId ? friend?.addresseeId : friend?.requesterId || '';
  const friendName = friend?.username || 'Friend';

  const ledger = ledgerData?.friendLedger || previousLedgerData?.friendLedger;
  const netBalance = Number(ledger?.netBalance || 0);
  const pendingReceivable = Number(ledger?.pendingReceivable || 0);
  const pendingPayable = Number(ledger?.pendingPayable || 0);
  const pendingNet = pendingReceivable - pendingPayable;
  const transactions: LedgerTx[] = (ledger?.transactions || []).map((tx) => ({
    id: String(tx.id),
    lender_id: String(tx.lenderId || ''),
    borrower_id: String(tx.borrowerId || ''),
    friendship_id: String(tx.friendshipId || ''),
    amount: Number(tx.amount || 0),
    status: tx.status,
    due_date: String(tx.dueDate || ''),
  }));
  const pendingTransactions = transactions.filter((tx) => tx.status === 'pending');
  const historyTransactions = transactions.filter((tx) => tx.status !== 'pending');

  useEffect(() => {
    if (!ledgerError) {
      setApiError('');
      return;
    }
    if (previousLedgerData?.friendLedger) {
      setApiError('ক্যাশ করা হিসাব দেখানো হচ্ছে।');
      return;
    }
    setApiError('এই মুহূর্তে বন্ধুর হিসাব লোড করা যাচ্ছে না।');
  }, [ledgerError, previousLedgerData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !friendUserId) return;

    setLoading(true);
    setApiError('');
    try {
      await api.post('/api/transactions/', {
        lender_id: myId,
        borrower_id: friendUserId,
        friendship_id: ledgerFriendshipId,
        amount: Number(amount),
        due_date: dueDate || null,
        idempotency_key: crypto.randomUUID(),
      });
      setAmount('');
      setDueDate('');
    } catch {
      setApiError('ট্রানজ্যাকশন জমা দেওয়া যায়নি। আবার চেষ্টা করুন।');
    } finally {
      setLoading(false);
    }
  };

  const handleUnfriend = async () => {
    if (!friendUserId || unfriendLoading) {
      return;
    }
    if (!window.confirm(`Remove ${friendName} from your friends?`)) {
      return;
    }

    setUnfriendLoading(true);
    setApiError('');
    try {
      await api.post('/api/social/unfriend/', { user_id: friendUserId });
      navigate('/home');
    } catch {
      setApiError('এখন আনফ্রেন্ড করা যাচ্ছে না। আবার চেষ্টা করুন।');
    } finally {
      setUnfriendLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F3F4F6] pb-20">
      <div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 h-16 flex items-center gap-3">
          <button onClick={() => navigate('/home')} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors">
            <ArrowLeft size={24} />
          </button>
          <h1 className="font-bold text-xl" style={{ fontFamily: 'var(--font-display)' }}>
            {friendName}
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {(friendsLoading || ledgerLoading) && !ledger && <p className="text-sm text-[#6B7280]">বন্ধুর তথ্য লোড হচ্ছে...</p>}
        {friendsError && !friend && <p className="text-sm text-[#DC2626]">বন্ধুর প্রোফাইল লোড করা যাচ্ছে না।</p>}
        {apiError && <p className={`text-sm ${apiError.includes('cached') ? 'text-[#B45309]' : 'text-[#DC2626]'}`}>{apiError}</p>}

        <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
          <div className="flex justify-center mb-4">
            <Avatar name={friendName} size="large" />
          </div>
          <h2 className="font-bold text-xl mb-2" style={{ fontFamily: 'var(--font-display)' }}>
            {friendName}
          </h2>
          <p className="text-sm text-[#6B7280] mb-4">মোট হিসাব</p>
          <p className={`text-4xl font-medium ${netBalance >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`} style={{ fontFamily: 'var(--font-mono)' }}>
            {netBalance >= 0 ? '+' : '-'}TK {Math.abs(netBalance).toLocaleString()}
          </p>
          <p className="text-xs text-[#6B7280] mt-2">
            {pendingNet > 0
              ? 'আপনি টাকা পাবেন'
              : pendingNet < 0
                ? 'আপনাকে টাকা দিতে হবে'
                : netBalance > 0
                  ? 'আপনি টাকা পাবেন'
                  : netBalance < 0
                    ? 'আপনাকে টাকা দিতে হবে'
                    : 'কোনো বকেয়া নেই'}
          </p>
          {(pendingReceivable > 0 || pendingPayable > 0) && (
            <div className="mt-4 rounded-xl bg-[#FEF3C7] border border-[#FCD34D] p-3 text-left">
              <p className="text-xs font-medium text-[#92400E]">পেন্ডিং অনুমোদন</p>
              {pendingNet > 0 && <p className="text-sm text-[#92400E] mt-1">আপনি পাবেন: TK {Math.abs(pendingNet).toLocaleString()}</p>}
              {pendingNet < 0 && <p className="text-sm text-[#92400E] mt-1">আপনাকে নিশ্চিত করতে হবে: TK {Math.abs(pendingNet).toLocaleString()}</p>}
              <p className="text-xs text-[#92400E] mt-2">পেন্ডিং ট্রানজ্যাকশন: {pendingTransactions.length}</p>
            </div>
          )}
          <button
            onClick={() => void handleUnfriend()}
            disabled={!friendUserId || unfriendLoading}
            className={`mt-5 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              !friendUserId || unfriendLoading
                ? 'bg-[#E5E7EB] text-[#6B7280]'
                : 'bg-[#FEE2E2] text-[#B91C1C] hover:bg-[#FECACA]'
            }`}
          >
            {unfriendLoading ? 'সরানো হচ্ছে...' : 'Unfriend'}
          </button>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="font-bold text-lg mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            টাকা দিন / যোগ করুন
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-[#111827] mb-2 font-medium">পরিমাণ</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl text-[#111827]" style={{ fontFamily: 'var(--font-mono)' }}>
                  TK
                </span>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0"
                  className="w-full h-16 pl-16 pr-4 bg-[#F3F4F6] border border-[#E5E7EB] rounded-xl text-center text-2xl focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5] transition-all"
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}
                  required
                />
              </div>
            </div>

            <Input type="date" label="শেষ তারিখ (ঐচ্ছিক)" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            <Button type="submit" fullWidth className="mt-6" disabled={loading || !friendUserId}>
              {loading ? 'জমা হচ্ছে...' : 'Submit'}
            </Button>
          </form>
        </div>

        <div>
          <h3 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            ট্রানজ্যাকশন হিসাব
          </h3>
          <div className="space-y-3">
            {historyTransactions.map((transaction, index) => {
              const isGave = transaction.lender_id === myId;
              return (
                <motion.div
                  key={transaction.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15, delay: index * 0.05 }}
                  className="bg-white rounded-2xl p-4 shadow-sm"
                >
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-full ${isGave ? 'bg-[#FEE2E2]' : 'bg-[#D1FAE5]'}`}>
                      {isGave ? <ArrowUp size={20} className="text-[#EF4444]" /> : <ArrowDown size={20} className="text-[#10B981]" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-1">
                        <p className={`text-lg font-medium ${isGave ? 'text-[#EF4444]' : 'text-[#10B981]'}`} style={{ fontFamily: 'var(--font-mono)' }}>
                          {isGave ? '-' : '+'}TK {Number(transaction.amount).toLocaleString()}
                        </p>
                        <StatusChip status={transaction.status} />
                      </div>
                      <p className="text-xs text-[#9CA3AF]">
                        {transaction.due_date ? new Date(transaction.due_date).toLocaleDateString('en-GB') : 'শেষ তারিখ নেই'}
                      </p>
                    </div>
                  </div>
                </motion.div>
              );
            })}
            {historyTransactions.length === 0 && (
              <div className="bg-white rounded-2xl p-4 shadow-sm">
                <p className="text-sm text-[#6B7280]">এখনও নিশ্চিত বা বাতিল ট্রানজ্যাকশন নেই।</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
