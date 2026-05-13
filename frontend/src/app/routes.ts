import { createBrowserRouter } from 'react-router';
import Login from './pages/Login';
import Home from './pages/Home';
import FriendDetail from './pages/FriendDetail';
import FindFriends from './pages/FindFriends';
import Profile from './pages/Profile';
import NotFound from './pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Login
  },
  {
    path: '/home',
    Component: Home
  },
  {
    path: '/friend/:id',
    Component: FriendDetail
  },
  {
    path: '/friends',
    Component: FindFriends
  },
  {
    path: '/profile',
    Component: Profile
  },
  {
    path: '*',
    Component: NotFound
  }
]);
