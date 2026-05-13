interface BalanceChipProps {
  amount: number;
  type: 'owed' | 'owe';
}

export function BalanceChip({ amount, type }: BalanceChipProps) {
  const isPositive = type === 'owed';

  const styles = isPositive
    ? 'bg-[#D1FAE5] text-[#065F46] border-[#6EE7B7]'
    : 'bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]';

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full border text-[13px] ${styles}`}
      style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}
    >
      {isPositive ? '+' : '-'}৳{Math.abs(amount).toLocaleString()}
    </span>
  );
}
