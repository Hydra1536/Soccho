import { Home, Users, User } from 'lucide-react';
import { Link, useLocation } from 'react-router';

export function BottomNav() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/home', icon: Home, label: 'Home' },
    { path: '/friends', icon: Users, label: 'Friends' },
    { path: '/profile', icon: User, label: 'Profile' }
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#E5E7EB] safe-area-inset-bottom z-50">
      <div className="flex justify-around items-center h-16 max-w-md mx-auto">
        {navItems.map(({ path, icon: Icon, label }) => (
          <Link
            key={path}
            to={path}
            className={`flex flex-col items-center justify-center w-full h-full transition-colors relative ${
              isActive(path) ? 'text-[#4F46E5]' : 'text-[#6B7280]'
            }`}
          >
            <Icon size={24} strokeWidth={2} />
            {isActive(path) && (
              <div className="absolute bottom-0 w-1.5 h-1.5 rounded-full bg-[#4F46E5]" />
            )}
          </Link>
        ))}
      </div>
    </nav>
  );
}
