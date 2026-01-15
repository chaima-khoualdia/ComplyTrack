import { LayoutDashboard, Bell, LogOut, Users, Building2, TrendingUp } from 'lucide-react';
import { AuthUser, UserRole } from '../AuthContext';

interface NavigationProps {
  user: AuthUser;
  onNavigate: (page: string) => void;
  onLogout: () => void;
  currentPage: string;
}

export function Navigation({ user, onNavigate, onLogout, currentPage }: NavigationProps) {
  const getNavLinks = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return [
          { id: 'admin-dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { id: 'reminders', label: 'Reminders', icon: Bell }
        ];
      case 'investor':
        return [
          { id: 'investor-dashboard', label: 'Portfolio', icon: TrendingUp }
        ];
      case 'owner':
        return [
          { id: 'owner-dashboard', label: 'Compliance', icon: Building2 }
        ];
      case 'worker':
        return [
          { id: 'worker-dashboard', label: 'My Tasks', icon: Users }
        ];
      default:
        return [];
    }
  };

  const navLinks = getNavLinks(user.role);

  return (
    <nav className="sticky top-0 bg-white border-b border-gray-200 z-50 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3">
              <img src="/src/assets/Logo_NoSlogan_Dark.svg" alt="ComplyTrack" className="h-8 w-auto" />
              <div className="hidden md:flex flex-col">
                <span className="text-xl font-bold text-gray-900">ComplyTrack</span>
                <span className="text-xs text-gray-500">Master compliance. Protect investments.</span>
              </div>
            </div>

            <div className="hidden md:flex items-center space-x-1">
              {navLinks.map((link) => {
                const Icon = link.icon;
                return (
                  <button
                    key={link.id}
                    onClick={() => onNavigate(link.id)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                      currentPage === link.id
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{link.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-gray-900">{user.name}</div>
              <div className="text-xs text-gray-500 capitalize">{user.role}</div>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline font-medium">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}