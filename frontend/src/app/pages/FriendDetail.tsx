import { useState } from 'react';
import { ArrowLeft, ArrowUp, ArrowDown } from 'lucide-react';
import { useParams, useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { Avatar } from '../components/Avatar';
import { StatusChip } from '../components/StatusChip';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { BottomNav } from '../components/BottomNav';

const transactions = [
  {
    id: 1,
    amount: 5000,
    direction: 'gave' as const,
    date: '2026-05-10',
    status: 'confirmed' as const,
    note: 'Emergency medical expenses'
  },
  {
    id: 2,
    amount: 2000,
    direction: 'received' as const,
    date: '2026-05-08',
    status: 'confirmed' as const,
    note: 'Partial repayment'
  },
  {
    id: 3,
    amount: 3000,
    direction: 'gave' as const,
    date: '2026-05-05',
    status: 'pending' as const,
    note: 'Business investment'
  },
  {
    id: 4,
    amount: 1500,
    direction: 'received' as const,
    date: '2026-05-01',
    status: 'denied' as const,
    note: 'Disputed payment'
  }
];

export default function FriendDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [amount, setAmount] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [note, setNote] = useState('');

  const friendName = 'Rahim Khan';
  const netBalance = 5000;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Transaction submitted:', { amount, dueDate, note });
    setAmount('');
    setDueDate('');
    setNote('');
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
            {friendName}
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Hero Card */}
        <div className="bg-white rounded-2xl p-6 shadow-sm text-center">
          <div className="flex justify-center mb-4">
            <Avatar name={friendName} size="large" />
          </div>
          <h2 className="font-bold text-xl mb-2" style={{ fontFamily: 'var(--font-display)' }}>
            {friendName}
          </h2>
          <p className="text-sm text-[#6B7280] mb-4">Net Balance</p>
          <p
            className={`text-4xl font-medium ${netBalance >= 0 ? 'text-[#10B981]' : 'text-[#EF4444]'}`}
            style={{ fontFamily: 'var(--font-mono)' }}
          >
            {netBalance >= 0 ? '+' : '-'}৳{Math.abs(netBalance).toLocaleString()}
          </p>
          <p className="text-xs text-[#6B7280] mt-2">
            {netBalance >= 0 ? 'They owe you' : 'You owe them'}
          </p>
        </div>

        {/* Give/Lend Money Form */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <h3 className="font-bold text-lg mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            Give / Lend Money
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-[#111827] mb-2 font-medium">Amount</label>
              <div className="relative">
                <span
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl text-[#111827]"
                  style={{ fontFamily: 'var(--font-mono)' }}
                >
                  ৳
                </span>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0"
                  className="w-full h-16 pl-12 pr-4 bg-[#F3F4F6] border border-[#E5E7EB] rounded-xl text-center text-2xl focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5] transition-all"
                  style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}
                  required
                />
              </div>
            </div>

            <Input
              type="date"
              label="Due Date (optional)"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />

            <div>
              <label className="block text-sm text-[#111827] mb-2 font-medium">Note</label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="What's this for?"
                className="w-full h-20 px-4 py-3 bg-[#F3F4F6] border border-[#E5E7EB] rounded-xl text-[#111827] resize-none focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5] transition-all"
              />
            </div>

            <Button type="submit" fullWidth className="mt-6">
              Submit
            </Button>
          </form>
        </div>

        {/* Transaction Timeline */}
        <div>
          <h3 className="font-bold text-lg mb-3" style={{ fontFamily: 'var(--font-display)' }}>
            Transaction History
          </h3>
          <div className="space-y-3">
            {transactions.map((transaction, index) => (
              <motion.div
                key={transaction.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15, delay: index * 0.05 }}
                className="bg-white rounded-2xl p-4 shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-full ${transaction.direction === 'gave' ? 'bg-[#FEE2E2]' : 'bg-[#D1FAE5]'}`}>
                    {transaction.direction === 'gave' ? (
                      <ArrowUp size={20} className="text-[#EF4444]" />
                    ) : (
                      <ArrowDown size={20} className="text-[#10B981]" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-1">
                      <p
                        className={`text-lg font-medium ${transaction.direction === 'gave' ? 'text-[#EF4444]' : 'text-[#10B981]'}`}
                        style={{ fontFamily: 'var(--font-mono)' }}
                      >
                        {transaction.direction === 'gave' ? '-' : '+'}৳{transaction.amount.toLocaleString()}
                      </p>
                      <StatusChip status={transaction.status} />
                    </div>
                    <p className="text-sm text-[#6B7280] mb-1">{transaction.note}</p>
                    <p className="text-xs text-[#9CA3AF]">{new Date(transaction.date).toLocaleDateString('en-GB')}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
