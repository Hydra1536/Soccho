interface StatusChipProps {
  status: 'pending' | 'confirmed' | 'denied';
}

export function StatusChip({ status }: StatusChipProps) {
  const styles = {
    pending: 'bg-[#FEF3C7] text-[#92400E] border-[#FCD34D]',
    confirmed: 'bg-[#D1FAE5] text-[#065F46] border-[#6EE7B7]',
    denied: 'bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]'
  };

  const labels = {
    pending: 'Pending',
    confirmed: 'Confirmed',
    denied: 'Denied'
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}
