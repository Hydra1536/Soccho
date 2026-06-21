import { createBrowserRouter, Navigate } from "react-router";
import { hasAccessToken } from "../lib/api";
import ChangePassword from "./pages/ChangePassword";
import FindFriends from "./pages/FindFriends";
import ForgotPassword from "./pages/ForgotPassword";
import FriendDetail from "./pages/FriendDetail";
import Home from "./pages/Home";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";

function AuthGuard({ children }: { children: JSX.Element }) {
	if (!hasAccessToken()) {
		return <Navigate to="/" replace />;
	}
	return children;
}

function GuardedHome() {
	return (
		<AuthGuard>
			<Home />
		</AuthGuard>
	);
}

function GuardedFriendDetail() {
	return (
		<AuthGuard>
			<FriendDetail />
		</AuthGuard>
	);
}

function GuardedFriends() {
	return (
		<AuthGuard>
			<FindFriends />
		</AuthGuard>
	);
}

function GuardedProfile() {
	return (
		<AuthGuard>
			<Profile />
		</AuthGuard>
	);
}

function GuardedChangePassword() {
	return (
		<AuthGuard>
			<ChangePassword />
		</AuthGuard>
	);
}

const routeConfig = [
	{
		path: "/",
		Component: Login,
	},
	{
		path: "/forgot-password",
		Component: ForgotPassword,
	},
	{
		path: "/home",
		Component: GuardedHome,
	},
	{
		path: "/friend/:id",
		Component: GuardedFriendDetail,
	},
	{
		path: "/friends",
		Component: GuardedFriends,
	},
	{
		path: "/profile",
		Component: GuardedProfile,
	},
	{
		path: "/change-password",
		Component: GuardedChangePassword,
	},
	{
		path: "*",
		Component: NotFound,
	},
];

export const router = createBrowserRouter(routeConfig, {
	basename: import.meta.env.BASE_URL || "/",
});
