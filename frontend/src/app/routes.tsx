import { Navigate, createBrowserRouter } from 'react-router';
import Login from './pages/Login';
import Home from './pages/Home';
import FriendDetail from './pages/FriendDetail';
import FindFriends from './pages/FindFriends';
import Profile from './pages/Profile';
import NotFound from './pages/NotFound';
import ForgotPassword from './pages/ForgotPassword';
import ChangePassword from './pages/ChangePassword';
import { hasAccessToken } from '../lib/api';

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

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Login,
  },
  {
    path: '/forgot-password',
    Component: ForgotPassword,
  },
  {
    path: '/home',
    Component: GuardedHome,
  },
  {
    path: '/friend/:id',
    Component: GuardedFriendDetail,
  },
  {
    path: '/friends',
    Component: GuardedFriends,
  },
  {
    path: '/profile',
    Component: GuardedProfile,
  },
  {
    path: '/change-password',
    Component: GuardedChangePassword,
  },
  {
    path: '*',
    Component: NotFound,
  },
]);
