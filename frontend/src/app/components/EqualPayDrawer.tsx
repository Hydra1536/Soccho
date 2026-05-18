import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Calculator, X } from 'lucide-react';

type Person = {
  name: string;
  amount: string;
};

type Settlement = {
  from: string;
  to: string;
  amount: string;
};

type EqualPayDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
};

function calculateSettlement(people: Array<{ name: string; amount: number }>) {
  const total = people.reduce((sum, person) => sum + person.amount, 0);
  const avg = total / people.length;

  const pos: Array<{ name: string; amt: number }> = [];
  const neg: Array<{ name: string; amt: number }> = [];

  people.forEach((person) => {
    const diff = +(person.amount - avg).toFixed(2);
    if (diff > 0) {
      pos.push({ name: person.name, amt: diff });
    }
    if (diff < 0) {
      neg.push({ name: person.name, amt: -diff });
    }
  });

  pos.sort((a, b) => b.amt - a.amt);
  neg.sort((a, b) => b.amt - a.amt);

  const settlements: Settlement[] = [];
  let i = 0;
  let j = 0;

  while (i < pos.length && j < neg.length) {
    const settle = Math.min(pos[i].amt, neg[j].amt);
    settlements.push({
      from: neg[j].name,
      to: pos[i].name,
      amount: settle.toFixed(2),
    });

    pos[i].amt = +(pos[i].amt - settle).toFixed(2);
    neg[j].amt = +(neg[j].amt - settle).toFixed(2);

    if (pos[i].amt <= 0) {
      i += 1;
    }
    if (neg[j].amt <= 0) {
      j += 1;
    }
  }

  return { avg: avg.toFixed(2), settlements };
}

export function EqualPayDrawer({ isOpen, onClose }: EqualPayDrawerProps) {
  const [countInput, setCountInput] = useState('3');
  const [count, setCount] = useState(3);
  const [people, setPeople] = useState<Person[]>([
    { name: '', amount: '' },
    { name: '', amount: '' },
    { name: '', amount: '' },
  ]);
  const [result, setResult] = useState<{ avg: string; settlements: Settlement[] } | null>(null);
  const [error, setError] = useState('');
  const resultRef = useRef<HTMLDivElement | null>(null);

  const peopleCount = useMemo(() => Math.max(2, Number(count) || 2), [count]);

  const ensureCount = (nextCount: number) => {
    setPeople((prev) => {
      const normalized = Math.max(2, nextCount);
      if (prev.length === normalized) {
        return prev;
      }
      if (prev.length > normalized) {
        return prev.slice(0, normalized);
      }
      const extra = Array.from({ length: normalized - prev.length }, () => ({ name: '', amount: '' }));
      return [...prev, ...extra];
    });
  };

  const handleCountConfirm = () => {
    const numeric = Math.max(2, Number(countInput.replace(/\D/g, '')) || 2);
    setCount(numeric);
    setCountInput(String(numeric));
    ensureCount(numeric);
    setResult(null);
    setError('');
  };

  const handlePersonChange = (index: number, key: keyof Person, value: string) => {
    setPeople((prev) =>
      prev.map((person, idx) => {
        if (idx !== index) {
          return person;
        }
        if (key === 'amount') {
          const normalized = value.replace(/[^0-9.-]/g, '');
          return { ...person, amount: normalized };
        }
        return { ...person, [key]: value };
      })
    );
    setResult(null);
    setError('');
  };

  const handleCalculate = () => {
    const normalized = people.slice(0, peopleCount).map((person, idx) => ({
      name: person.name.trim() || `Person ${idx + 1}`,
      amount: Number(person.amount || 0),
    }));

    const hasInvalid = normalized.some((person) => Number.isNaN(person.amount));
    if (hasInvalid) {
      setError('Please enter valid numbers for all amounts.');
      setResult(null);
      return;
    }

    const calculated = calculateSettlement(normalized);
    setResult(calculated);
    setError('');
  };

  useEffect(() => {
    if (!result) {
      return;
    }
    resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [result]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }} className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="fixed left-0 top-0 bottom-0 w-[85%] max-w-md bg-white z-50 shadow-2xl rounded-r-2xl overflow-y-auto"
          >
            <div className="p-4 border-b border-[#E5E7EB] flex items-center justify-between sticky top-0 bg-white">
              <div className="flex items-center gap-2">
                <Calculator size={20} className="text-[#111827]" />
                <h2 className="font-bold text-lg" style={{ fontFamily: 'var(--font-display)' }}>
                  Soccho
                </h2>
              </div>
              <button onClick={onClose} className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="p-4 space-y-4">
              <div className="bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl p-3 text-sm text-[#374151]">
                <p>
                  একসাথে ঘোরাঘুরি বা খাওয়া-দাওয়ার খরচ সমানভাবে ভাগ করা নিয়ে চিন্তিত? কে কত টাকা ফেরত
                  পাবে বা কাকে কত দিতে হবে, তার একটি পরিষ্কার তালিকা পেতে সবার নাম এবং কে কত খরচ করেছে তা
                  যোগ করুন।
                </p>
                <p className="mt-2">আড্ডা হবে প্রাণখুলে, আর হিসাব হবে Soccho-তে!✨</p>
              </div>

              <div className="bg-white border border-[#E5E7EB] rounded-xl p-4">
                <label className="block text-sm text-[#111827] mb-2 font-medium">Number of People</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    inputMode="numeric"
                    value={countInput}
                    onChange={(event) => setCountInput(event.target.value.replace(/\D/g, ''))}
                    className="flex-1 h-11 px-3 bg-[#F3F4F6] border border-[#E5E7EB] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5]"
                  />
                  <button
                    onClick={handleCountConfirm}
                    className="h-11 px-4 rounded-lg bg-[#111827] text-white text-sm font-medium hover:bg-black transition-colors"
                  >
                    Confirm
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {people.slice(0, peopleCount).map((person, idx) => (
                  <div key={idx} className="bg-white border border-[#E5E7EB] rounded-xl p-4">
                    <label className="block text-sm text-[#111827] mb-2 font-medium">Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Batman"
                      value={person.name}
                      onChange={(event) => handlePersonChange(idx, 'name', event.target.value)}
                      className="w-full h-10 px-3 bg-[#F3F4F6] border border-[#E5E7EB] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5]"
                    />
                    <label className="block text-sm text-[#111827] mt-3 mb-2 font-medium">Paid Amount (Taka)</label>
                    <input
                      type="text"
                      inputMode="numeric"
                      placeholder="e.g. 600"
                      value={person.amount}
                      onChange={(event) => handlePersonChange(idx, 'amount', event.target.value)}
                      className="w-full h-10 px-3 bg-[#F3F4F6] border border-[#E5E7EB] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5]"
                    />
                  </div>
                ))}
              </div>

              {error && <p className="text-sm text-[#DC2626]">{error}</p>}

              <button
                onClick={handleCalculate}
                className="w-full h-11 rounded-xl bg-[#111827] text-white font-medium hover:bg-black transition-colors"
              >
                Calculate Settlement
              </button>

              {result && (
                <div ref={resultRef} className="bg-white border border-[#E5E7EB] rounded-xl p-4">
                  <h3 className="font-bold text-[#111827]">Average Payment: {result.avg} taka</h3>
                  {result.settlements.length === 0 && (
                    <p className="text-sm text-[#6B7280] mt-2">Everyone already paid equally.</p>
                  )}
                  {result.settlements.map((item, index) => (
                    <p key={index} className="text-sm text-[#374151] mt-3">
                      <strong>{item.from}</strong> will pay <strong>{item.amount}</strong> taka to <strong>{item.to}</strong>
                    </p>
                  ))}
                </div>
              )}

              <p className="text-center text-xs text-[#6B7280]">© 2026 MD Rezaul Karim.</p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
