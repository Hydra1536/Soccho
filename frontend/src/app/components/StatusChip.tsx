interface StatusChipProps {
	status:
		| "pending"
		| "confirmed"
		| "denied"
		| "pending_verification"
		| "agreed"
		| "rejected"
		| "settled";
}

export function StatusChip({ status }: StatusChipProps) {
	const styles = {
		pending: "bg-[#FEF3C7] text-[#92400E] border-[#FCD34D]",
		confirmed: "bg-[#D1FAE5] text-[#065F46] border-[#6EE7B7]",
		denied: "bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]",
		pending_verification: "bg-[#FEF3C7] text-[#92400E] border-[#FCD34D]",
		agreed: "bg-[#D1FAE5] text-[#065F46] border-[#6EE7B7]",
		rejected: "bg-[#FEE2E2] text-[#991B1B] border-[#FCA5A5]",
		settled: "bg-[#DBEAFE] text-[#1D4ED8] border-[#93C5FD]",
	};

	const labels = {
		pending: "Pending",
		confirmed: "Confirmed",
		denied: "Denied",
		pending_verification: "Pending Verification",
		agreed: "Agreed",
		rejected: "Rejected",
		settled: "Settled",
	};

	return (
		<span
			className={`inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-medium ${styles[status]}`}
		>
			{labels[status]}
		</span>
	);
}
