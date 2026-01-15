import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Users, Building2, Bell, Settings, BarChart3, FileText, Search, Plus, Trash2, Eye, CheckCircle, XCircle, Play, Square, RefreshCw, Clock, TrendingUp } from 'lucide-react';
import * as api from '../api';

interface AdminManagementPageProps {
  onBack: () => void;
  onCreateUser: () => void;
  onCreateStartup: () => void;
  onNavigate: (page: string) => void;
}

type TabType = 'users' | 'startups' | 'reminders' | 'scheduler' | 'statistics' | 'requests';

export function AdminManagementPage({ onBack, onCreateUser, onCreateStartup, onNavigate }: AdminManagementPageProps) {
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [schedulerRunning, setSchedulerRunning] = useState<boolean>(true);
  const [selectedReminders, setSelectedReminders] = useState<number[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [startups, setStartups] = useState<any[]>([]);
  const [reminders, setReminders] = useState<any[]>([]);
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [adminStats, setAdminStats] = useState<any | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const [userList, startupList, allReminders, scheduler, stats] = await Promise.all([
          api.listUsers().catch(() => []),
          api.listAllStartups().catch(() => []),
          api.listAllReminders().catch(() => []),
          api.getSchedulerStatus().catch(() => ({ running: false, jobs: [] })),
          api.getAdminStats().catch(() => null),
        ]);
  // Admin stats
  setAdminStats(stats);

        // Map users to UI shape
        setUsers(
          (userList || []).map((u: any) => ({
            id: u.id,
            name: `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email,
            email: u.email,
            role: u.role,
            createdDate: u.created_at ? new Date(u.created_at).toISOString().slice(0, 10) : ''
          }))
        );

        // Map startups to UI shape
        setStartups(
          (startupList || []).map((s: any) => ({
            id: s.id,
            name: s.name,
            matricule: s.matricule_fiscal,
            founder_id: s.founder_id,
            badgeStatus: (s.badge_status || 'pending').toLowerCase() === 'green' ? 'compliant' : ((s.badge_status || 'pending').toLowerCase() === 'red' ? 'at-risk' : 'pending'),
            workers: 0,
          }))
        );

        // Map reminders to UI shape; attach startupName via lookup
        const startupNameById: Record<number, string> = {};
        (startupList || []).forEach((s: any) => { startupNameById[s.id] = s.name; });
        setReminders(
          (allReminders || []).map((r: any) => {
            const dueDate = r.reminder_date ? new Date(r.reminder_date) : null;
            const today = new Date();
            const daysUntilDue = dueDate ? Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)) : null;
            let title = r.message || 'Reminder';
            if (title.includes(' due by ')) {
              title = title.split(' due by ')[0];
            }
            return {
              id: r.id,
              startupName: startupNameById[r.startup_id] || `Startup ${r.startup_id}`,
              dueDate: r.reminder_date,
              daysUntilDue: daysUntilDue ?? 0,
              sent: (r.status || '').toLowerCase() === 'sent',
              title,
              startup_id: r.startup_id,
              status: r.status,
            };
          })
        );

        setSchedulerRunning(!!scheduler?.running);

        // Aggregate pending requests across all startups (admin view)
        const pending = await Promise.all(
          (startupList || []).slice(0, 50).map(async (s: any) => {
            const rs = await api.listPendingRequests(s.id).catch(() => []);
            return rs.map((req: any) => ({
              id: req.id,
              workerName: req.worker_name,
              email: req.worker_email,
              startupName: s.name,
              status: req.status,
              date: req.created_at,
              startup_id: s.id,
            }));
          })
        );
        setRequests(pending.flat());
      } catch (e: any) {
        setError(e?.message || 'Failed to load admin management data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const filteredStartups = startups.filter(startup =>
    startup.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    startup.matricule.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredReminders = reminders.filter(reminder =>
    reminder.startupName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    reminder.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.deleteUser(userId);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (e: any) {
      alert(e?.message || 'Failed to delete user');
    }
  };

  const handleDeleteReminder = async (reminderId: number) => {
    if (!confirm('Are you sure you want to delete this reminder?')) return;
    try {
      await api.deleteReminder(reminderId);
      setReminders((prev) => prev.filter((r) => r.id !== reminderId));
    } catch (e: any) {
      alert(e?.message || 'Failed to delete reminder');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedReminders.length === 0) return;
    if (!confirm(`Delete ${selectedReminders.length} selected reminders?`)) return;
    try {
      await Promise.all(selectedReminders.map((id) => api.deleteReminder(id)));
      setReminders((prev) => prev.filter((r) => !selectedReminders.includes(r.id)));
      setSelectedReminders([]);
    } catch (e: any) {
      alert(e?.message || 'Failed to bulk delete reminders');
    }
  };

  const handleBulkMarkSent = async () => {
    if (selectedReminders.length === 0) return;
    try {
      await Promise.all(selectedReminders.map((id) => api.markReminderSent(id)));
      setReminders((prev) => prev.map((r) => selectedReminders.includes(r.id) ? { ...r, sent: true, status: 'sent' } : r));
      setSelectedReminders([]);
    } catch (e: any) {
      alert(e?.message || 'Failed to bulk mark reminders as sent');
    }
  };

  const toggleScheduler = async () => {
    try {
      if (schedulerRunning) {
        await api.stopScheduler();
      } else {
        await api.startScheduler();
      }
      const status = await api.getSchedulerStatus();
      setSchedulerRunning(!!status?.running);
    } catch (e: any) {
      alert(e?.message || 'Failed to toggle scheduler');
    }
  };

  const handleApproveRequest = async (requestId: number) => {
    try {
      await api.approveRequest(requestId);
      setRequests((prev) => prev.map((r) => r.id === requestId ? { ...r, status: 'approved' } : r));
    } catch (e: any) {
      alert(e?.message || 'Failed to approve request');
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    if (!confirm('Are you sure you want to reject this request?')) return;
    try {
      await api.rejectRequest(requestId, 'Rejected by admin');
      setRequests((prev) => prev.map((r) => r.id === requestId ? { ...r, status: 'rejected' } : r));
    } catch (e: any) {
      alert(e?.message || 'Failed to reject request');
    }
  };

  const tabs = [
    { id: 'users' as TabType, label: 'User Management', icon: Users },
    { id: 'startups' as TabType, label: 'Startup Management', icon: Building2 },
    { id: 'reminders' as TabType, label: 'Reminder Management', icon: Bell },
    { id: 'scheduler' as TabType, label: 'Scheduler Control', icon: Settings },
    { id: 'statistics' as TabType, label: 'Statistics', icon: BarChart3 },
    { id: 'requests' as TabType, label: 'Requests', icon: FileText },
  ];

  const userStats = useMemo(() => ({
    total: users.length,
    admin: users.filter(u => (u.role || '').toLowerCase() === 'admin').length,
    investor: users.filter(u => (u.role || '').toLowerCase() === 'investor').length,
    owner: users.filter(u => (u.role || '').toLowerCase() === 'owner').length,
    worker: users.filter(u => (u.role || '').toLowerCase() === 'worker').length,
  }), [users]);

  const startupStats = useMemo(() => ({
    total: startups.length,
    compliant: startups.filter(s => s.badgeStatus === 'compliant').length,
    pending: startups.filter(s => s.badgeStatus === 'pending').length,
    atRisk: startups.filter(s => s.badgeStatus === 'at-risk').length,
  }), [startups]);

  return (
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={onBack}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </button>

      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">System Management</h1>
        <p className="text-gray-600">Comprehensive admin controls and monitoring</p>
      </div>

      {/* Loading / Error states */}
      {loading && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg text-gray-700">
          Loading management data...
        </div>
      )}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 mb-8 overflow-hidden">
        <div className="flex overflow-x-auto scrollbar-hide">
          {tabs.map((tab, index) => {
            const Icon = tab.icon;
            return (
              <div key={tab.id} className="flex items-center">
                <button
                  onClick={() => {
                    setActiveTab(tab.id);
                    setSearchTerm('');
                    setRoleFilter('all');
                  }}
                  className={`flex items-center justify-center space-x-3 px-10 py-6 font-bold text-lg transition-all border-b-4 whitespace-nowrap group ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600 bg-blue-50'
                      : 'border-transparent text-gray-600 hover:text-blue-600 hover:bg-gray-50'
                  }`}
                >
                  <div className={`p-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-200 text-blue-700'
                      : 'bg-gray-100 text-gray-600 group-hover:bg-blue-100 group-hover:text-blue-600'
                  }`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
                {index < tabs.length - 1 && <div className="w-px h-8 bg-gray-200" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
        {/* USER MANAGEMENT TAB */}
        {activeTab === 'users' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
              <button
                onClick={onCreateUser}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Create User</span>
              </button>
            </div>

            {/* User Stats */}
            <div className="grid grid-cols-5 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-600 mb-1">Total Users</p>
                <p className="text-2xl font-bold text-gray-900">{userStats.total}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                <p className="text-sm text-red-600 mb-1">Admins</p>
                <p className="text-2xl font-bold text-red-700">{userStats.admin}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <p className="text-sm text-blue-600 mb-1">Investors</p>
                <p className="text-2xl font-bold text-blue-700">{userStats.investor}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <p className="text-sm text-green-600 mb-1">Owners</p>
                <p className="text-2xl font-bold text-green-700">{userStats.owner}</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <p className="text-sm text-purple-600 mb-1">Workers</p>
                <p className="text-2xl font-bold text-purple-700">{userStats.worker}</p>
              </div>
            </div>

            {/* Search and Filter */}
            <div className="flex space-x-4 mb-6">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                <option value="all">All Roles</option>
                <option value="admin">Admin</option>
                <option value="investor">Investor</option>
                <option value="owner">Owner</option>
                <option value="worker">Worker</option>
              </select>
            </div>

            {/* User Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Email</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Role</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Created</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{user.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{user.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          user.role === 'admin' ? 'bg-red-100 text-red-700' :
                          user.role === 'investor' ? 'bg-blue-100 text-blue-700' :
                          user.role === 'owner' ? 'bg-green-100 text-green-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>
                          {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{user.createdDate}</td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => alert(`View details for ${user.name}`)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete User"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* STARTUP MANAGEMENT TAB */}
        {activeTab === 'startups' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Startup Management</h2>
              <button
                onClick={onCreateStartup}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Create Startup</span>
              </button>
            </div>

            {/* Startup Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-600 mb-1">Total Startups</p>
                <p className="text-2xl font-bold text-gray-900">{startupStats.total}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <p className="text-sm text-green-600 mb-1">Compliant</p>
                <p className="text-2xl font-bold text-green-700">{startupStats.compliant}</p>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                <p className="text-sm text-yellow-600 mb-1">Pending</p>
                <p className="text-2xl font-bold text-yellow-700">{startupStats.pending}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                <p className="text-sm text-red-600 mb-1">At Risk</p>
                <p className="text-2xl font-bold text-red-700">{startupStats.atRisk}</p>
              </div>
            </div>

            {/* Search */}
            <div className="mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name or matricule..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>
            </div>

            {/* Startup Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Name</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Matricule</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Founder</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Badge Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Workers</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredStartups.map((startup) => (
                    <tr key={startup.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{startup.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{startup.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 font-mono">{startup.matricule}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{startup.founder}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          startup.badgeStatus === 'compliant' ? 'bg-green-100 text-green-700' :
                          startup.badgeStatus === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {startup.badgeStatus.charAt(0).toUpperCase() + startup.badgeStatus.slice(1)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{startup.workers}</td>
                      <td className="px-4 py-3 text-sm">
                        <button
                          onClick={() => alert(`View stats for ${startup.name}`)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="View Stats"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* REMINDER MANAGEMENT TAB */}
        {activeTab === 'reminders' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Reminder Management</h2>
              <div className="flex space-x-2">
                {selectedReminders.length > 0 && (
                  <>
                    <button
                      onClick={handleBulkMarkSent}
                      className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-green-700 transition-colors flex items-center space-x-2"
                    >
                      <CheckCircle className="w-4 h-4" />
                      <span>Mark Sent ({selectedReminders.length})</span>
                    </button>
                    <button
                      onClick={handleBulkDelete}
                      className="bg-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-700 transition-colors flex items-center space-x-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Delete ({selectedReminders.length})</span>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-600 mb-1">Total Reminders</p>
                <p className="text-2xl font-bold text-gray-900">{reminders.length}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <p className="text-sm text-green-600 mb-1">Sent</p>
                <p className="text-2xl font-bold text-green-700">{reminders.filter(r => r.sent).length}</p>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                <p className="text-sm text-yellow-600 mb-1">Pending</p>
                <p className="text-2xl font-bold text-yellow-700">{reminders.filter(r => !r.sent).length}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                <p className="text-sm text-red-600 mb-1">Due Soon (7 days)</p>
                <p className="text-2xl font-bold text-red-700">{reminders.filter(r => r.daysUntilDue <= 7).length}</p>
              </div>
            </div>

            {/* Search */}
            <div className="mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by startup name or reminder title..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>
            </div>

            {/* Reminder Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedReminders.length === reminders.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedReminders(reminders.map(r => r.id));
                          } else {
                            setSelectedReminders([]);
                          }
                        }}
                        className="rounded"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Startup</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Title</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Due Date</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Days Until Due</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredReminders.map((reminder) => (
                    <tr key={reminder.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedReminders.includes(reminder.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedReminders([...selectedReminders, reminder.id]);
                            } else {
                              setSelectedReminders(selectedReminders.filter(id => id !== reminder.id));
                            }
                          }}
                          className="rounded"
                        />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{reminder.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{reminder.startupName}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{reminder.title}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{reminder.dueDate}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          reminder.daysUntilDue <= 7 ? 'bg-red-100 text-red-700' :
                          reminder.daysUntilDue <= 14 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {reminder.daysUntilDue} days
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {reminder.sent ? (
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                            Sent
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
                            Pending
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => alert(`View reminder ${reminder.id}`)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteReminder(reminder.id)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* SCHEDULER CONTROL TAB */}
        {activeTab === 'scheduler' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Scheduler Control</h2>

            {/* Scheduler Status */}
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Scheduler Status</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-4 py-2 rounded-full font-semibold ${
                      schedulerRunning ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {schedulerRunning ? '● Running' : '● Stopped'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Last Run:</span>
                    <span className="font-medium text-gray-900">2025-01-11 10:00:00</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Next Run:</span>
                    <span className="font-medium text-gray-900">2025-01-11 11:00:00</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Emails Today:</span>
                    <span className="font-bold text-blue-600">12</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Emails This Week:</span>
                    <span className="font-bold text-blue-600">87</span>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Control Panel</h3>
                <div className="space-y-3">
                  <button
                    onClick={toggleScheduler}
                    className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-semibold transition-colors ${
                      schedulerRunning
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                  >
                    {schedulerRunning ? (
                      <>
                        <Square className="w-5 h-5" />
                        <span>Stop Scheduler</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5" />
                        <span>Start Scheduler</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => alert('Running scheduler now...')}
                    className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Play className="w-5 h-5" />
                    <span>Run Now</span>
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Restart scheduler?')) {
                        alert('Scheduler restarted');
                      }
                    }}
                    className="w-full bg-yellow-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-yellow-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <RefreshCw className="w-5 h-5" />
                    <span>Restart Scheduler</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STATISTICS TAB */}
        {activeTab === 'statistics' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">System Statistics</h2>

            {/* System Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-lg p-6 border-2 border-blue-300">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-900">Total Users</span>
                  <Users className="w-6 h-6 text-gray-800" />
                </div>
                <div className="text-4xl font-bold text-gray-900">{adminStats?.total_users ?? users.length}</div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl shadow-lg p-6 border-2 border-green-300">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-900">Total Startups</span>
                  <Building2 className="w-6 h-6 text-gray-800" />
                </div>
                <div className="text-4xl font-bold text-gray-900">{adminStats?.total_startups ?? startups.length}</div>
              </div>
              <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl shadow-lg p-6 border-2 border-yellow-300">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-900">Active Reminders</span>
                  <Bell className="w-6 h-6 text-gray-800" />
                </div>
                <div className="text-4xl font-bold text-gray-900">{reminders.filter((r) => (r.status || '').toLowerCase() !== 'cancelled').length}</div>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl shadow-lg p-6 border-2 border-purple-300">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-bold text-gray-900">Pending Requests</span>
                  <FileText className="w-6 h-6 text-gray-800" />
                </div>
                <div className="text-4xl font-bold text-gray-900">{requests.filter((r) => (r.status || '').toLowerCase() === 'pending').length}</div>
              </div>
            </div>

            {/* Search Stats */}
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Investor Stats Lookup</h3>
                <div className="space-y-4">
                  <input
                    type="number"
                    placeholder="Enter Investor ID..."
                    className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                  <button className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                    View Portfolio Stats
                  </button>
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-gray-500">Enter an investor ID to view their portfolio statistics</p>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Startup Stats Lookup</h3>
                <div className="space-y-4">
                  <input
                    type="number"
                    placeholder="Enter Startup ID..."
                    className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                  <button className="w-full bg-green-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors">
                    View Compliance Stats
                  </button>
                  <div className="bg-gray-50 rounded-lg p-4 text-center">
                    <p className="text-sm text-gray-500">Enter a startup ID to view detailed compliance statistics</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Growth Stats */}
            <div className="mt-8 bg-white border border-gray-200 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
                Growth Trends
              </h3>
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">User Growth (30d)</p>
                  <p className="text-3xl font-bold text-green-600">+24%</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Startup Growth (30d)</p>
                  <p className="text-3xl font-bold text-blue-600">+18%</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Compliance Rate</p>
                  <p className="text-3xl font-bold text-purple-600">78%</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* REQUEST MANAGEMENT TAB */}
        {activeTab === 'requests' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Request Management</h2>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-600 mb-1">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900">{requests.length}</p>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                <p className="text-sm text-yellow-600 mb-1">Pending</p>
                <p className="text-2xl font-bold text-yellow-700">{requests.filter(r => (r.status || '').toLowerCase() === 'pending').length}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                <p className="text-sm text-green-600 mb-1">Approved</p>
                <p className="text-2xl font-bold text-green-700">{requests.filter(r => (r.status || '').toLowerCase() === 'approved').length}</p>
              </div>
            </div>

            {/* Request Table */}
            <div className="w-full overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">ID</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Worker Name</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Email</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Startup</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {requests.map((request) => (
                    <tr key={request.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{request.id}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{request.workerName}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{request.email}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{request.startupName}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{request.date}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                          (request.status || '').toLowerCase() === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                          (request.status || '').toLowerCase() === 'approved' ? 'bg-green-100 text-green-700' :
                          (request.status || '').toLowerCase() === 'rejected' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {request.status ? request.status.charAt(0).toUpperCase() + request.status.slice(1) : 'Unknown'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex gap-1 whitespace-nowrap">
                          {(request.status || '').toLowerCase() === 'pending' && (
                            <>
                              <button
                                onClick={() => handleApproveRequest(request.id)}
                                className="p-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                                title="Approve"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleRejectRequest(request.id)}
                                className="p-1.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                                title="Reject"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          {(request.status || '').toLowerCase() !== 'pending' && (
                            <span className="text-xs text-gray-500">-</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {requests.length === 0 && (
              <div className="text-center py-12 bg-gray-50 rounded-lg">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No pending requests</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}