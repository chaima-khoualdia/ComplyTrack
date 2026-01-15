import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Building2, TrendingUp, Calendar, UserPlus, PlusCircle, Settings, FileText } from 'lucide-react';
import { Navigation } from './Navigation';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface AdminStats {
  total_users: number;
  total_startups: number;
  total_investors: number;
  nbr_admins: number;
  nbr_owners: number;
  nbr_workers: number;
  scheduled_jobs: number;
  email_success_rate: number;
}

export function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [procedures, setProcedures] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleNavigate = (page: string) => {
    if (page === 'reminders') {
      navigate('/reminders');
    } else if (page === 'admin-dashboard') {
      navigate('/dashboard/admin');
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('[AdminDashboard] Starting fetch...');
      const statsResp = await api.getAdminStats();
      console.log('[AdminDashboard] Fetched stats RAW:', JSON.stringify(statsResp, null, 2));
      
      // Use backend response directly - no transformation needed
      setStats(statsResp as AdminStats);
      
      // Fetch recent activity (completed procedures, accepted workers, etc)
      const recentActiv = await api.getRecentActivity(10);
      setProcedures(recentActiv);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load admin stats';
      console.error('[AdminDashboard] Error:', errorMsg, err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const statsList = [
    { label: 'Total Users', value: stats?.total_users || 0, icon: Users, color: 'blue' },
    { label: 'Startups', value: stats?.total_startups || 0, icon: Building2, color: 'green' },
    { label: 'Investors', value: stats?.total_investors || 0, icon: TrendingUp, color: 'purple' },
    { label: 'Total Roles', value: (stats?.nbr_admins || 0) + (stats?.nbr_owners || 0) + (stats?.nbr_workers || 0), icon: Calendar, color: 'orange' }
  ];

  const recentActivity = procedures.slice(0, 10).map((activity) => {
    let user = '';
    let action = '';
    let type = 'info';
    
    if (activity.type === 'procedure_completed') {
      user = `Founder (${activity.startup_name})`;
      action = `Completed ${activity.procedure_name}`;
      type = 'success';
    } else if (activity.type === 'worker_accepted') {
      user = `${activity.startup_name} Owner`;
      action = `Accepted ${activity.worker_name}`;
      type = 'success';
    }
    
    const timeAgo = new Date(activity.completed_at).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
    
    return {
      user,
      action,
      time: timeAgo,
      type
    };
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {user && <Navigation user={user} onNavigate={handleNavigate} onLogout={logout} currentPage="admin-dashboard" />}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-600">System overview and management</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
          <button onClick={fetchAdminData} className="ml-2 underline font-semibold">
            Retry
          </button>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <button
          onClick={() => navigate('/admin/create-user')}
          className="bg-blue-600 text-white rounded-xl shadow-xl p-8 hover:bg-blue-700 transition-all transform hover:-translate-y-1 active:translate-y-0"
        >
          <div className="flex items-center space-x-6">
            <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
              <UserPlus className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <h3 className="text-2xl font-bold text-white mb-1">Create User</h3>
              <p className="text-blue-100 text-sm">Add new user or investor</p>
            </div>
          </div>
        </button>

        <button
          onClick={() => navigate('/admin/create-startup')}
          className="bg-green-600 text-white rounded-xl shadow-xl p-8 hover:bg-green-700 transition-all transform hover:-translate-y-1 active:translate-y-0"
        >
          <div className="flex items-center space-x-6">
            <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
              <PlusCircle className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <h3 className="text-2xl font-bold text-white mb-1">Create Startup</h3>
              <p className="text-green-100 text-sm">Register new startup</p>
            </div>
          </div>
        </button>

        <button
          onClick={() => navigate('/admin/management')}
          className="bg-purple-600 text-white rounded-xl shadow-xl p-8 hover:bg-purple-700 transition-all transform hover:-translate-y-1 active:translate-y-0"
        >
          <div className="flex items-center space-x-6">
            <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
              <Settings className="w-6 h-6 text-white" />
            </div>
            <div className="text-left">
              <h3 className="text-2xl font-bold text-white mb-1">System Management</h3>
              <p className="text-purple-100 text-sm">Advanced admin controls and monitoring</p>
            </div>
          </div>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsList.map((stat, index) => {
            const Icon = stat.icon;
            const colorClasses = {
              blue: 'bg-blue-100 text-blue-600',
              green: 'bg-green-100 text-green-600',
              purple: 'bg-purple-100 text-purple-600',
              orange: 'bg-orange-100 text-orange-600'
            };
            return (
              <div key={index} className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
                <div className="flex items-center justify-between mb-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-3xl font-bold text-gray-900">{stat.value}</span>
                </div>
                <p className="text-gray-600 font-medium">{stat.label}</p>
              </div>
            );
          })}
        </div>

      {/* Reminder Scheduler Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Reminder Scheduler</h2>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-600">Active</span>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-semibold text-gray-900">Daily Email Schedule</p>
                <p className="text-sm text-gray-600">Automated reminders sent daily</p>
              </div>
              <span className="text-lg font-bold text-blue-600">9:00 AM</span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-semibold text-gray-900">Next Scheduled Run</p>
                <p className="text-sm text-gray-600">Tomorrow morning</p>
              </div>
              <span className="text-sm font-medium text-gray-700">In 14 hours</span>
            </div>
          </div>
        </div>

        {/* Role Management */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Role Distribution</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-900">Admins</span>
              <span className="font-bold text-blue-600">{stats?.nbr_admins || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-900">Owners</span>
              <span className="font-bold text-blue-600">{stats?.nbr_owners || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-900">Workers</span>
              <span className="font-bold text-blue-600">{stats?.nbr_workers || 0}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-900">Investors</span>
              <span className="font-bold text-blue-600">{stats?.total_investors || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Recent Activity</h2>
          <button className="flex items-center space-x-2 px-4 py-2 bg-blue-50 text-blue-600 hover:bg-blue-100 font-medium rounded-lg transition-colors border border-blue-200">
            <FileText className="w-4 h-4" />
            <span>View All Logs</span>
          </button>
        </div>
        <div className="space-y-3">
          {recentActivity.length === 0 && (
            <div className="p-4 bg-gray-50 rounded-lg text-gray-600">No recent activity.</div>
          )}
          {recentActivity.map((activity, index) => {
            const typeColors = {
              success: 'bg-green-100 text-green-700',
              info: 'bg-blue-100 text-blue-700',
              warning: 'bg-yellow-100 text-yellow-700'
            };
            return (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">{activity.user}</p>
                  <p className="text-sm text-gray-600">{activity.action}</p>
                </div>
                <div className="text-right">
                  <span className={`text-xs px-3 py-1 rounded-full ${typeColors[activity.type as keyof typeof typeColors]}`}>
                    {activity.type}
                  </span>
                  <p className="text-sm text-gray-500 mt-1">{activity.time}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      </div>
    </>
  );
}
