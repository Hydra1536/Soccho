import { ArrowLeft, Lock, LogOut, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import api, {
	EMAIL_KEY,
	getApiErrorMessage,
	USERNAME_KEY,
} from "../../lib/api";
import { fetchCurrentUser, logout } from "../../lib/auth";
import { Avatar } from "../components/Avatar";
import { BottomNav } from "../components/BottomNav";

type PendingVerificationRow = {
	id: string;
	friendship_id: string;
	friendship_route_id?: string;
	amount: string;
	due_date?: string | null;
	note?: string;
	lender_name?: string;
};

export default function Profile() {
	const navigate = useNavigate();
	const [userName, setUserName] = useState(
		localStorage.getItem(USERNAME_KEY) || "",
	);
	const [userEmail, setUserEmail] = useState(
		localStorage.getItem(EMAIL_KEY) || "",
	);
	const [profileError, setProfileError] = useState("");
	const [canChangePassword, setCanChangePassword] = useState(false);
	const [loyaltyScore, setLoyaltyScore] = useState<number>(0);
	const [pendingVerifications, setPendingVerifications] = useState<
		PendingVerificationRow[]
	>([]);
	const [actingId, setActingId] = useState("");

	const loadPendingVerifications = async () => {
		try {
			const { data } = await api.get<{ results?: PendingVerificationRow[] }>(
				"/api/transactions/pending-verifications/",
			);
			setPendingVerifications(Array.isArray(data?.results) ? data.results : []);
		} catch {
			setPendingVerifications([]);
		}
	};

	useEffect(() => {
		let isMounted = true;

		const loadProfile = async () => {
			try {
				const profile = await fetchCurrentUser();
				if (!isMounted) {
					return;
				}
				setUserName(profile.username);
				setUserEmail(profile.email);
				setCanChangePassword(profile.has_password);
				setProfileError("");
			} catch (error) {
				if (!isMounted) {
					return;
				}
				setProfileError(
					getApiErrorMessage(
						error,
						"Unable to load profile details right now.",
					),
				);
			}
		};

		const loadLoyaltyScore = async () => {
			try {
				const { data } = await api.get<{ loyalty_score?: number }>(
					"/api/transactions/loyalty-score/",
				);
				if (!isMounted) {
					return;
				}
				const raw = Number(data?.loyalty_score ?? 0);
				setLoyaltyScore(
					Math.max(0, Math.min(100, Number.isFinite(raw) ? raw : 0)),
				);
			} catch {
				if (!isMounted) {
					return;
				}
				setLoyaltyScore(0);
			}
		};

		void loadProfile();
		void loadLoyaltyScore();
		void loadPendingVerifications();

		return () => {
			isMounted = false;
		};
	}, []);

	const handleResolve = async (
		transactionId: string,
		action: "agree" | "disagree",
	) => {
		const userId = localStorage.getItem("user_id") || "";
		setActingId(transactionId);
		try {
			await api.post(`/api/transactions/${transactionId}/resolve/`, {
				borrower_id: userId,
				action,
			});
			await loadPendingVerifications();
		} catch (error) {
			setProfileError(
				getApiErrorMessage(
					error,
					`Unable to ${action} this transaction right now.`,
				),
			);
		} finally {
			setActingId("");
		}
	};

	const handleLogout = async () => {
		await logout();
		navigate("/");
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
						Profile
					</h1>
				</div>
			</div>

			<div className="max-w-md mx-auto px-4 py-6 space-y-6">
				<div className="bg-white rounded-2xl p-6 shadow-sm text-center">
					<div className="flex justify-center mb-4">
						<Avatar name={userName || "User"} size="large" />
					</div>
					<h2
						className="font-bold text-xl mb-1"
						style={{ fontFamily: "var(--font-display)" }}
					>
						{userName || "Loading profile..."}
					</h2>
					<p className="text-sm text-[#6B7280]">
						{userEmail || "Fetching your account details..."}
					</p>
					<div className="mt-4">
						<p className="text-xs text-[#6B7280] mb-1">Loyalty Score</p>
						<div className="h-2 rounded-full bg-[#E5E7EB] overflow-hidden">
							<div
								className="h-full bg-[#4F46E5] rounded-full transition-all"
								style={{ width: `${loyaltyScore}%` }}
							/>
						</div>
						<p className="text-sm text-[#111827] mt-2 font-medium">
							{loyaltyScore.toFixed(1)} / 100
						</p>
					</div>
					{profileError && (
						<p className="mt-3 text-sm text-[#EF4444]">{profileError}</p>
					)}
				</div>

				<div className="bg-white rounded-2xl p-6 shadow-sm">
					<div className="flex items-center gap-2 mb-4">
						<ShieldCheck size={18} className="text-[#B45309]" />
						<h3
							className="font-bold text-lg"
							style={{ fontFamily: "var(--font-display)" }}
						>
							Pending Verifications
						</h3>
					</div>
					<div className="space-y-3">
						{pendingVerifications.map((item) => {
							const isActing = actingId === item.id;
							return (
								<div
									key={item.id}
									className="rounded-2xl border border-[#FCD34D] bg-[#FFFBEB] p-4"
								>
									<p className="text-sm font-semibold text-[#92400E]">
										{item.lender_name || "A friend"} logged TK{" "}
										{Number(item.amount || 0).toLocaleString()}
									</p>
									<p className="text-xs text-[#92400E] mt-1">
										Due:{" "}
										{item.due_date
											? new Date(item.due_date).toLocaleDateString("en-GB")
											: "No due date"}
									</p>
									{item.note && (
										<p className="text-sm text-[#78350F] mt-2">{item.note}</p>
									)}
									<div className="flex gap-2 mt-3">
										<button
											onClick={() => void handleResolve(item.id, "agree")}
											disabled={isActing}
											className={`px-3 py-2 rounded-lg text-sm font-medium ${isActing ? "bg-[#A7F3D0] text-[#065F46]" : "bg-[#10B981] text-white hover:bg-[#059669]"}`}
										>
											Agree
										</button>
										<button
											onClick={() => void handleResolve(item.id, "disagree")}
											disabled={isActing}
											className={`px-3 py-2 rounded-lg text-sm font-medium ${isActing ? "bg-[#FECACA] text-[#991B1B]" : "bg-[#EF4444] text-white hover:bg-[#DC2626]"}`}
										>
											Disagree
										</button>
										<button
											onClick={() =>
												navigate(
													`/friend/${item.friendship_route_id || item.friendship_id}?tab=verifications`,
												)
											}
											className="px-3 py-2 rounded-lg text-sm font-medium bg-[#111827] text-white hover:bg-black"
										>
											Open friend profile
										</button>
									</div>
								</div>
							);
						})}
						{pendingVerifications.length === 0 && (
							<p className="text-sm text-[#6B7280]">
								No pending transaction verifications right now.
							</p>
						)}
					</div>
				</div>

				<div className="bg-white rounded-2xl overflow-hidden shadow-sm">
					{canChangePassword && (
						<button
							className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#F3F4F6] transition-colors border-b border-[#E5E7EB]"
							onClick={() => navigate("/change-password")}
						>
							<Lock size={20} className="text-[#6B7280]" />
							<span className="flex-1 text-left text-[#111827]">
								Change Password
							</span>
						</button>
					)}
					<button
						onClick={handleLogout}
						className="w-full px-4 py-4 flex items-center gap-3 hover:bg-[#FEE2E2] transition-colors"
					>
						<LogOut size={20} className="text-[#EF4444]" />
						<span className="flex-1 text-left text-[#EF4444]">Log Out</span>
					</button>
				</div>
			</div>

			<BottomNav />
		</div>
	);
}
