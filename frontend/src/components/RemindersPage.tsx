import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Mail, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { Navigation } from './Navigation';
import { getDomainKeyFromProc } from './domainUtils';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface Deadline {
  title: string;
  domain: string;
  date: string;
  days: number;
  priority: 'high' | 'medium' | 'low';
  notified: boolean;
  startupName?: string;
}

interface NotificationItem {
  title: string;
  recipient: string;
  sent: string;
  status: string;
}

export function RemindersPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [schedulerStatus, setSchedulerStatus] = useState({
    active: true,
    schedule: 'Daily at 9:00 AM',
    lastRun: '',
    nextRun: '',
    totalSent: 0,
    successRate: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleNavigate = (page: string) => {
    if (page === 'reminders') {
      navigate('/reminders');
    } else if (page === 'admin-dashboard') {
      navigate('/dashboard/admin');
    }
  };

  const formatDate = (date: Date) => date.toLocaleString(undefined, { hour: 'numeric', minute: '2-digit', month: 'short', day: 'numeric' });

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const now = new Date();

        // Fetch scheduler status (admin-only endpoint but safe for all, will return running/jobs)
        try {
          const sched = await api.getSchedulerStatus();
          const running = !!sched?.running;
          // get earliest next_run if any
          const nextRunIso: string | undefined = sched?.jobs?.[0]?.next_run || undefined;
          const nextRun = nextRunIso ? formatDate(new Date(nextRunIso)) : '';
          setSchedulerStatus((prev) => ({
            ...prev,
            active: running,
            nextRun
          }));
        } catch {}

        if (user?.role === 'admin') {
          // Admin view: aggregate upcoming reminders and recent notifications across startups
          const startups = await api.listAllStartups();
          const startupIds = Array.isArray(startups) ? startups.map((s: any) => s.id) : [];
          const startupNameById = new Map<number, string>();
          (startups || []).forEach((s: any) => {
            if (s && typeof s.id !== 'undefined') startupNameById.set(Number(s.id), s.name || `Startup ${s.id}`);
          });

          // Fetch from all startups, but limit requests to first 20 for performance
          const sampleIds = startupIds.slice(0, 20);

          const upcomingByStartup = await Promise.all(
            sampleIds.map(async (sid) => ({
              sid,
              items: await api.getUpcomingReminders(sid, 365).catch(() => [])
            }))
          );
          const upcoming = upcomingByStartup.flatMap(({ sid, items }) => items.map((r: any) => {
            const dueTime = Date.parse(r.reminder_date);
            const days = Number.isNaN(dueTime) ? 0 : Math.max(0, Math.round((dueTime - Date.now()) / (1000 * 60 * 60 * 24)));
            let priority: 'high' | 'medium' | 'low' = 'medium';
            if (days <= 7) priority = 'high';
            else if (days <= 30) priority = 'medium';
            else priority = 'low';
            const title = (r.message && r.message.split(' due by ')[0]) || 'Procedure';
            return {
              title,
              domain: '',
              date: r.reminder_date,
              days,
              priority,
              notified: (r.status || '').toLowerCase() !== 'pending',
              startupName: startupNameById.get(Number(sid)) || undefined
            } as Deadline;
          }));
          setDeadlines(upcoming.sort((a, b) => a.days - b.days));

          // Recent notifications: pull reminders and show those marked as sent/overdue
          const allRemindersArrays = await Promise.all(
            sampleIds.map((sid) => api.getRemindersByStartup(sid).catch(() => []))
          );
          const allReminders = allRemindersArrays.flat();
          const recent = allReminders
            .filter((r: any) => (r.status || '').toLowerCase() !== 'pending')
            .sort((a: any, b: any) => Date.parse(b.reminder_date) - Date.parse(a.reminder_date))
            .slice(0, 5)
            .map((r: any) => {
              const title = (r.message && r.message.split(' due by ')[0]) || 'Procedure Reminder';
              const statusLabel = (r.status || '').toLowerCase() === 'sent' ? 'complete' : 'pending';
              return {
                title,
                recipient: 'Founder',
                sent: formatDate(new Date(r.reminder_date)),
                status: statusLabel
              } as NotificationItem;
            });
          setNotifications(recent);
        } else {
          // Non-admin view: derive from the user's startup procedures
          let resolvedStartupId = (user as any)?.startupId || null;
          if (!resolvedStartupId) {
            const mine = await api.listMyStartups();
            if (Array.isArray(mine) && mine.length > 0) {
              resolvedStartupId = mine[0].id;
            }
          }

          if (!resolvedStartupId) {
            throw new Error('No startup found for reminders.');
          }

          const procedures = await api.listProcedures(resolvedStartupId);
          // Try to resolve startup name for display
          let startupName: string | undefined = undefined;
          try {
            const myStartups = await api.listMyStartups();
            const found = (myStartups || []).find((s: any) => Number(s.id) === Number(resolvedStartupId));
            startupName = found?.name || undefined;
          } catch {}

          const derivedDeadlines: Deadline[] = (procedures || []).map((proc: any) => {
            const time = Date.parse(proc.due_date || proc.deadline || '');
            const days = Number.isNaN(time) ? 30 : Math.max(0, Math.round((time - Date.now()) / (1000 * 60 * 60 * 24)));
            let priority: 'high' | 'medium' | 'low' = 'medium';
            if (days <= 7) priority = 'high';
            else if (days <= 30) priority = 'medium';
            else priority = 'low';

            return {
              title: proc.procedure_name || 'Procedure',
              domain: getDomainKeyFromProc(proc),
              date: proc.due_date || 'No due date',
              days,
              priority,
              notified: (proc.status || '').toLowerCase() === 'notified',
              startupName
            };
          });

          setDeadlines(derivedDeadlines.sort((a, b) => a.days - b.days).slice(0, 6));

          const totalSteps = procedures.reduce((acc: number, proc: any) => acc + (proc.total_steps || 0), 0);
          const completedSteps = procedures.reduce(
            (acc: number, proc: any) => acc + (proc.completed_steps || 0),
            0
          );

          const next = new Date();
          next.setDate(now.getDate() + 1);

          setSchedulerStatus({
            active: true,
            schedule: 'Daily at 9:00 AM',
            lastRun: formatDate(now),
            nextRun: formatDate(next),
            totalSent: completedSteps,
            successRate: totalSteps === 0 ? 0 : Number(((completedSteps / totalSteps) * 100).toFixed(1))
          });

          const derivedNotifications: NotificationItem[] = (procedures || []).flatMap((proc: any) =>
            (proc.steps || []).slice(0, 1).map((step: any) => ({
              title: `${proc.procedure_name || 'Procedure'}: ${step.name || 'Step'}`,
              recipient: proc.owner_email || 'team@startup.com',
              sent: formatDate(now),
              status: (proc.completed_step_ids || []).includes(step.id) ? 'complete' : 'pending'
            }))
          );
          setNotifications(derivedNotifications.slice(0, 5));
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load reminders';
        console.error('[RemindersPage] Load error:', msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [user]);

  const summary = useMemo(() => {
    const high = deadlines.filter((d) => d.priority === 'high').length;
    const medium = deadlines.filter((d) => d.priority === 'medium').length;
    const low = deadlines.filter((d) => d.priority === 'low').length;
    return { high, medium, low };
  }, [deadlines]);

  return (
    <>
      {user && <Navigation user={user} onNavigate={handleNavigate} onLogout={logout} currentPage="reminders" />}
      <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Reminders & Notifications</h1>
        <p className="text-gray-600">Automated reminder system powered by live compliance data</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">{error}</div>
      )}

      {/* Scheduler Status */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Email Scheduler Status</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${schedulerStatus.active ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className={`text-sm font-semibold ${schedulerStatus.active ? 'text-green-600' : 'text-red-600'}`}>
              {schedulerStatus.active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Schedule</span>
            </div>
            <p className="text-xl font-bold text-blue-600">{schedulerStatus.schedule}</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center space-x-2 mb-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-green-900">Last Run</span>
            </div>
            <p className="text-lg font-bold text-green-600">{schedulerStatus.lastRun}</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center space-x-2 mb-2">
              <Calendar className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-900">Next Run</span>
            </div>
            <p className="text-lg font-bold text-purple-600">{schedulerStatus.nextRun}</p>
          </div>
          <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
            <div className="flex items-center space-x-2 mb-2">
              <Mail className="w-5 h-5 text-indigo-600" />
              <span className="text-sm font-medium text-indigo-900">Success Rate</span>
            </div>
            <p className="text-xl font-bold text-indigo-600">{schedulerStatus.successRate}%</p>
          </div>
        </div>
      </div>

      {/* Upcoming Deadlines Timeline */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 mb-8">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold text-gray-900">Upcoming Deadlines Timeline</h2>
          <div className="text-sm text-gray-600">High: {summary.high} • Medium: {summary.medium} • Low: {summary.low}</div>
        </div>
        {isLoading && <p className="text-gray-600">Loading deadlines...</p>}
        {!isLoading && deadlines.length === 0 && (
          <p className="text-gray-600">No deadlines available yet.</p>
        )}
        <div className="space-y-4">
          {deadlines.map((deadline, index) => (
            <div
              key={index}
              className="relative pl-8 pb-4 border-l-2 border-gray-200 last:border-l-0 last:pb-0"
            >
              <div className={`absolute left-0 -translate-x-1/2 w-4 h-4 rounded-full ${
                deadline.priority === 'high' ? 'bg-red-500' :
                deadline.priority === 'medium' ? 'bg-yellow-500' :
                'bg-blue-500'
              }`}></div>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-1">
                    <h3 className="font-bold text-gray-900">{deadline.title}</h3>
                    {deadline.notified && (
                      <span className="flex items-center space-x-1 text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                        <Mail className="w-3 h-3" />
                        <span>Notified</span>
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{deadline.domain} • {deadline.date}{deadline.startupName ? ` • ${deadline.startupName}` : ''}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    deadline.priority === 'high' ? 'bg-red-100 text-red-700' :
                    deadline.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {deadline.days} days
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Notifications */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Notifications Sent</h2>
        {isLoading && <p className="text-gray-600">Loading notifications...</p>}
        {!isLoading && notifications.length === 0 && (
          <p className="text-gray-600">No notifications sent yet.</p>
        )}
        <div className="space-y-3">
          {notifications.map((notification, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Mail className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{notification.title}</p>
                  <p className="text-sm text-gray-600">To: {notification.recipient}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center space-x-2 mb-1">
                  {notification.status === 'complete' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-yellow-600" />
                  )}
                  <span className={`text-xs font-medium capitalize ${notification.status === 'complete' ? 'text-green-600' : 'text-yellow-700'}`}>{notification.status}</span>
                </div>
                <p className="text-sm text-gray-500">{notification.sent}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      </div>
    </>
  );
}
