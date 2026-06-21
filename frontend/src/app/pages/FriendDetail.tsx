import { useApolloClient, useQuery } from "@apollo/client";
import {
	ArrowDown,
	ArrowLeft,
	ArrowUp,
	HandCoins,
	ReceiptText,
} from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { GET_FRIEND_LEDGER, GET_FRIENDS } from "../../graphql/queries";
import api from "../../lib/api";
import { toDeterministicFriendshipUuid } from "../../lib/friendshipKey";
import { Avatar } from "../components/Avatar";
import { BottomNav } from "../components/BottomNav";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { StatusChip } from "../components/StatusChip";

type LedgerEntry = {
	id: string;
	lenderId: string;
	borrowerId: string;
	friendshipId: string;
	amount: number;
	status: string;
	dueDate: string;
	note?: string;
	createdAt?: string;
};

type FriendNode = {
	friendshipId: string;
	requesterId: string;
	addresseeId: string;
	userId: string;
	username: string;
};

type PendingVerification = LedgerEntry;

type LedgerNode = {
	friendshipId: string;
	netBalance: number;
	pendingReceivable?: number;
	pendingPayable?: number;
	activeDueTotal?: number;
	counterpartOwesYou?: string;
	pendingVerifications?: PendingVerification[];
	transactions: LedgerEntry[];
};

export default function FriendDetail() {
	const { id } = useParams();
	const navigate = useNavigate();
	const apolloClient = useApolloClient();
	const verificationRef = useRef<HTMLDivElement | null>(null);
	const [amount, setAmount] = useState("");
	const [note, setNote] = useState("");
	const [dueDate, setDueDate] = useState("");
	const [loading, setLoading] = useState(false);
	const [repaymentLoading, setRepaymentLoading] = useState(false);
	const [unfriendLoading, setUnfriendLoading] = useState(false);
	const [apiError, setApiError] = useState("");
	const [actingVerificationId, setActingVerificationId] = useState("");

	const myId = localStorage.getItem("user_id") || "";
	const ledgerFriendshipId = toDeterministicFriendshipUuid(String(id || ""));

	const { data: friendsData, previousData: previousFriendsData } = useQuery<{
		friendList: FriendNode[];
	}>(GET_FRIENDS, {
		skip: !myId,
		context: { service: "social" },
	});

	const {
		data: ledgerData,
		previousData: previousLedgerData,
		loading: ledgerLoading,
		refetch,
	} = useQuery<{ friendLedger: LedgerNode }>(GET_FRIEND_LEDGER, {
		variables: { friendshipId: ledgerFriendshipId },
		skip: !id,
		context: { service: "transaction" },
		fetchPolicy: "cache-and-network",
	});

	const friends =
		friendsData?.friendList || previousFriendsData?.friendList || [];
	const friend = useMemo(
		() => friends.find((row) => String(row.friendshipId) === String(id)),
		[friends, id],
	);
	const friendUserId =
		friend?.requesterId === myId
			? friend?.addresseeId
			: friend?.requesterId || "";
	const friendName = friend?.username || "Friend";
	const ledger = ledgerData?.friendLedger || previousLedgerData?.friendLedger;
	const netBalance = Number(ledger?.netBalance || 0);
	const activeDueTotal = Number(ledger?.activeDueTotal || 0);
	const pendingVerifications = ledger?.pendingVerifications || [];
	const historyEntries = ledger?.transactions || [];
	const currentUserOwes = netBalance < 0;

	useEffect(() => {
		const params = new URLSearchParams(window.location.search);
		if (params.get("tab") === "verifications") {
			verificationRef.current?.scrollIntoView({
				behavior: "smooth",
				block: "start",
			});
		}
	}, []);

	const refreshLedger = async () => {
		await refetch();
		await apolloClient.refetchQueries({
			include: [GET_FRIENDS, GET_FRIEND_LEDGER],
		});
	};

	const handleLogTransaction = async (event: React.FormEvent) => {
		event.preventDefault();
		if (!id || !friendUserId) {
			return;
		}

		setLoading(true);
		setApiError("");
		try {
			await api.post("/api/transactions/", {
				lender_id: myId,
				borrower_id: friendUserId,
				friendship_id: ledgerFriendshipId,
				friendship_route_id: id,
				amount: Number(amount),
				due_date: dueDate || null,
				note,
				idempotency_key: crypto.randomUUID(),
			});
			setAmount("");
			setNote("");
			setDueDate("");
			await refreshLedger();
		} catch {
			setApiError("Unable to submit the transaction log right now.");
		} finally {
			setLoading(false);
		}
	};

	const handleRecordRepayment = async () => {
		if (!friendUserId || !amount) {
			return;
		}
		setRepaymentLoading(true);
		setApiError("");
		try {
			await api.post("/api/transactions/repayments/", {
				friendship_id: ledgerFriendshipId,
				friendship_route_id: id,
				payer_id: myId,
				payee_id: friendUserId,
				amount: Number(amount),
				note,
				idempotency_key: crypto.randomUUID(),
			});
			setAmount("");
			setNote("");
			await refreshLedger();
		} catch {
			setApiError("Unable to record the repayment right now.");
		} finally {
			setRepaymentLoading(false);
		}
	};

	const handleVerification = async (
		transactionId: string,
		action: "agree" | "disagree",
	) => {
		setActingVerificationId(transactionId);
		setApiError("");
		try {
			await api.post(`/api/transactions/${transactionId}/resolve/`, {
				borrower_id: myId,
				action,
			});
			await refreshLedger();
		} catch {
			setApiError(`Unable to ${action} this transaction right now.`);
		} finally {
			setActingVerificationId("");
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
		setApiError("");
		try {
			await api.post("/api/social/unfriend/", { user_id: friendUserId });
			localStorage.setItem("recently_unfriended", String(id || ""));
			await apolloClient.clearStore();
			navigate("/home");
		} catch {
			setApiError("Unable to unfriend this user right now.");
		} finally {
			setUnfriendLoading(false);
		}
	};

	return (
		<div className="min-h-screen bg-[#F3F4F6] pb-20">
			<div className="bg-white border-b border-[#E5E7EB] sticky top-0 z-10">
				<div className="max-w-md mx-auto px-4 h-16 flex items-center gap-3">
					<button
						onClick={() => navigate("/home")}
						className="p-2 hover:bg-[#F3F4F6] rounded-lg transition-colors"
					>
						<ArrowLeft size={24} />
					</button>
					<h1
						className="font-bold text-xl"
						style={{ fontFamily: "var(--font-display)" }}
					>
						{friendName}
					</h1>
				</div>
			</div>

			<div className="max-w-md mx-auto px-4 py-6 space-y-6">
				{ledgerLoading && !ledger && (
					<p className="text-sm text-[#6B7280]">Loading profile ledger...</p>
				)}
				{apiError && <p className="text-sm text-[#DC2626]">{apiError}</p>}

				<div className="bg-white rounded-2xl p-6 shadow-sm text-center">
					<div className="flex justify-center mb-4">
						<Avatar name={friendName} size="large" />
					</div>
					<h2
						className="font-bold text-xl mb-2"
						style={{ fontFamily: "var(--font-display)" }}
					>
						{friendName}
					</h2>
					<p className="text-sm text-[#6B7280] mb-4">Relationship ledger</p>
					<p
						className={`text-4xl font-medium ${netBalance >= 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}
						style={{ fontFamily: "var(--font-mono)" }}
					>
						{netBalance >= 0 ? "+" : "-"}TK{" "}
						{Math.abs(netBalance).toLocaleString()}
					</p>
					<p className="text-xs text-[#6B7280] mt-2">
						{ledger?.counterpartOwesYou ||
							(currentUserOwes
								? `You owe ${friendName}.`
								: `${friendName} owes you.`)}
					</p>
					{activeDueTotal > 0 && (
						<div className="mt-4 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] p-3 text-left">
							<p className="text-xs font-semibold text-[#065F46]">
								{friendName} owes you TK {activeDueTotal.toLocaleString()}
							</p>
							<p className="text-xs text-[#047857] mt-1">
								This reflects all active agreed due records after FIFO repayment
								allocation.
							</p>
						</div>
					)}
					<button
						onClick={() => void handleUnfriend()}
						disabled={!friendUserId || unfriendLoading}
						className={`mt-5 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
							!friendUserId || unfriendLoading
								? "bg-[#E5E7EB] text-[#6B7280]"
								: "bg-[#FEE2E2] text-[#B91C1C] hover:bg-[#FECACA]"
						}`}
					>
						{unfriendLoading ? "Removing..." : "Unfriend"}
					</button>
				</div>

				<div
					ref={verificationRef}
					className="bg-white rounded-2xl p-6 shadow-sm"
				>
					<div className="flex items-center gap-2 mb-4">
						<ReceiptText size={18} className="text-[#B45309]" />
						<h3
							className="font-bold text-lg"
							style={{ fontFamily: "var(--font-display)" }}
						>
							Pending Verifications
						</h3>
					</div>
					<div className="space-y-3">
						{pendingVerifications.map((item) => {
							const isActing = actingVerificationId === item.id;
							return (
								<div
									key={item.id}
									className="rounded-2xl border border-[#FCD34D] bg-[#FFFBEB] p-4"
								>
									<p className="text-sm font-semibold text-[#92400E]">
										TK {Number(item.amount).toLocaleString()}
									</p>
									<p className="text-xs text-[#92400E] mt-1">
										Due:{" "}
										{item.dueDate
											? new Date(item.dueDate).toLocaleDateString("en-GB")
											: "No due date"}
									</p>
									{item.note && (
										<p className="text-sm text-[#78350F] mt-2">{item.note}</p>
									)}
									<div className="flex gap-2 mt-3">
										<button
											onClick={() => void handleVerification(item.id, "agree")}
											disabled={isActing}
											className={`px-3 py-2 rounded-lg text-sm font-medium ${isActing ? "bg-[#A7F3D0] text-[#065F46]" : "bg-[#10B981] text-white hover:bg-[#059669]"}`}
										>
											Agree
										</button>
										<button
											onClick={() =>
												void handleVerification(item.id, "disagree")
											}
											disabled={isActing}
											className={`px-3 py-2 rounded-lg text-sm font-medium ${isActing ? "bg-[#FECACA] text-[#991B1B]" : "bg-[#EF4444] text-white hover:bg-[#DC2626]"}`}
										>
											Disagree
										</button>
									</div>
								</div>
							);
						})}
						{pendingVerifications.length === 0 && (
							<p className="text-sm text-[#6B7280]">
								No pending transaction verifications for this friend.
							</p>
						)}
					</div>
				</div>

				<div className="bg-white rounded-2xl p-6 shadow-sm">
					<h3
						className="font-bold text-lg mb-4"
						style={{ fontFamily: "var(--font-display)" }}
					>
						Record a transaction log
					</h3>
					<form onSubmit={handleLogTransaction} className="space-y-4">
						<div>
							<label className="block text-sm text-[#111827] mb-2 font-medium">
								Amount
							</label>
							<div className="relative">
								<span
									className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl text-[#111827]"
									style={{ fontFamily: "var(--font-mono)" }}
								>
									TK
								</span>
								<input
									type="number"
									value={amount}
									onChange={(event) => setAmount(event.target.value)}
									placeholder="0"
									className="w-full h-16 pl-16 pr-4 bg-[#F3F4F6] border border-[#E5E7EB] rounded-xl text-center text-2xl focus:outline-none focus:ring-2 focus:ring-[#4F46E5] focus:border-[#4F46E5]"
									style={{ fontFamily: "var(--font-mono)", fontWeight: 500 }}
									required
								/>
							</div>
						</div>

						<Input
							type="date"
							label="Due date"
							value={dueDate}
							onChange={(event) => setDueDate(event.target.value)}
						/>
						<Input
							label="Note"
							value={note}
							onChange={(event) => setNote(event.target.value)}
							placeholder="Optional context for this log"
						/>

						<div className="grid grid-cols-1 gap-3">
							<Button
								type="submit"
								fullWidth
								disabled={loading || !friendUserId}
							>
								{loading ? "Submitting..." : "Submit for verification"}
							</Button>
							<button
								type="button"
								onClick={() => void handleRecordRepayment()}
								disabled={
									repaymentLoading ||
									!friendUserId ||
									!amount ||
									!currentUserOwes
								}
								className={`h-11 rounded-xl text-sm font-medium transition-colors ${
									repaymentLoading || !amount || !currentUserOwes
										? "bg-[#E5E7EB] text-[#6B7280]"
										: "bg-[#111827] text-white hover:bg-black"
								}`}
							>
								{repaymentLoading
									? "Recording repayment..."
									: "Record repayment against oldest due"}
							</button>
						</div>
						{!currentUserOwes && (
							<p className="text-xs text-[#6B7280]">
								Repayment is enabled when you currently owe this friend.
							</p>
						)}
					</form>
				</div>

				<div>
					<h3
						className="font-bold text-lg mb-3"
						style={{ fontFamily: "var(--font-display)" }}
					>
						Ledger history
					</h3>
					<div className="space-y-3">
						{historyEntries.map((entry, index) => {
							const isRepayment = entry.status === "repayment";
							const isOutgoing = entry.lenderId === myId && !isRepayment;
							const icon = isRepayment ? (
								<HandCoins size={20} className="text-[#2563EB]" />
							) : isOutgoing ? (
								<ArrowUp size={20} className="text-[#EF4444]" />
							) : (
								<ArrowDown size={20} className="text-[#10B981]" />
							);
							const badgeBg = isRepayment
								? "bg-[#DBEAFE]"
								: isOutgoing
									? "bg-[#FEE2E2]"
									: "bg-[#D1FAE5]";
							const amountColor = isRepayment
								? "text-[#2563EB]"
								: isOutgoing
									? "text-[#EF4444]"
									: "text-[#10B981]";
							const createdText = entry.createdAt
								? new Date(entry.createdAt).toLocaleDateString("en-GB")
								: "";
							return (
								<motion.div
									key={entry.id}
									initial={{ opacity: 0, y: 20 }}
									animate={{ opacity: 1, y: 0 }}
									transition={{ duration: 0.15, delay: index * 0.04 }}
									className="bg-white rounded-2xl p-4 shadow-sm"
								>
									<div className="flex items-start gap-3">
										<div className={`p-2 rounded-full ${badgeBg}`}>{icon}</div>
										<div className="flex-1">
											<div className="flex items-start justify-between mb-1">
												<p
													className={`text-lg font-medium ${amountColor}`}
													style={{ fontFamily: "var(--font-mono)" }}
												>
													{isRepayment ? "" : isOutgoing ? "-" : "+"}TK{" "}
													{Number(entry.amount).toLocaleString()}
												</p>
												{isRepayment ? (
													<span className="text-xs rounded-full bg-[#DBEAFE] text-[#1D4ED8] px-2 py-1">
														Repayment
													</span>
												) : (
													<StatusChip
														status={
															entry.status as
																| "pending_verification"
																| "agreed"
																| "rejected"
																| "settled"
														}
													/>
												)}
											</div>
											<p className="text-xs text-[#9CA3AF]">
												{entry.dueDate
													? `Due ${new Date(entry.dueDate).toLocaleDateString("en-GB")}`
													: createdText || "No due date"}
											</p>
											{entry.note && (
												<p className="text-sm text-[#4B5563] mt-2">
													{entry.note}
												</p>
											)}
										</div>
									</div>
								</motion.div>
							);
						})}
						{historyEntries.length === 0 && (
							<div className="bg-white rounded-2xl p-4 shadow-sm">
								<p className="text-sm text-[#6B7280]">No ledger history yet.</p>
							</div>
						)}
					</div>
				</div>
			</div>

			<BottomNav />
		</div>
	);
}
