import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Circle, Calendar, AlertCircle } from 'lucide-react';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface TaskItem {
  id: string;
  title: string;
  completed: boolean;
  dueDate: string;
  priority: 'high' | 'medium' | 'low';
  domain: string;
  startupId: number;
  procedureId: number;
}

export function UserDashboard() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);

        let resolvedStartupId = (user as any)?.startupId || null;
        if (!resolvedStartupId) {
          const mine = await api.listMyStartups();
          if (Array.isArray(mine) && mine.length > 0) {
            resolvedStartupId = mine[0].id;
          }
        }

        if (!resolvedStartupId) {
          throw new Error('No startup found for this account.');
        }

        const procedures = await api.listProcedures(resolvedStartupId);
        const enrichedTasks: TaskItem[] = [];

        for (const proc of procedures || []) {
          (proc.steps || []).forEach((step: any) => {
            const due = proc.due_date || 'No due date';
            const time = Date.parse(due);
            const days = Number.isNaN(time) ? 30 : Math.max(0, Math.round((time - Date.now()) / (1000 * 60 * 60 * 24)));
            let priority: 'high' | 'medium' | 'low' = 'medium';
            if (days <= 7) priority = 'high';
            else if (days <= 30) priority = 'medium';
            else priority = 'low';

            enrichedTasks.push({
              id: String(step.id),
              title: `${proc.procedure_name || 'Procedure'}: ${step.name || 'Step'}`,
              completed: (proc.completed_step_ids || []).includes(step.id),
              dueDate: due,
              priority,
              domain: proc.domain,
              startupId: proc.startup_id ?? resolvedStartupId,
              procedureId: proc.procedure_id ?? proc.id
            });
          });
        }

        setTasks(enrichedTasks);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load tasks';
        console.error('[UserDashboard] Load error:', msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [user]);

  const handleToggle = async (id: string) => {
    try {
      const task = tasks.find((t) => t.id === id);
      if (!task) return;
      const newCompleted = !task.completed;
      await api.toggleProcedureStep(task.startupId, task.procedureId, Number(id), newCompleted);
      setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t)));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update task';
      console.error('[UserDashboard] Toggle error:', msg);
      setError(msg);
    }
  };

  const upcomingReminders = useMemo(() => {
    return tasks
      .map((task) => ({ title: task.title, date: task.dueDate, type: task.domain }))
      .slice(0, 5);
  }, [tasks]);

  const completedCount = tasks.filter((t) => t.completed).length;
  const pendingCount = tasks.length - completedCount;
  const highPriorityCount = tasks.filter((t) => !t.completed && t.priority === 'high').length;

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-gray-600">Loading your tasks...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">My Tasks</h1>
        <p className="text-gray-600">Your assigned compliance tasks and upcoming reminders</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">{error}</div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <Circle className="w-8 h-8 text-blue-600" />
            <span className="text-3xl font-bold text-gray-900">{pendingCount}</span>
          </div>
          <p className="text-gray-600 font-medium">Pending Tasks</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle2 className="w-8 h-8 text-green-600" />
            <span className="text-3xl font-bold text-gray-900">{completedCount}</span>
          </div>
          <p className="text-gray-600 font-medium">Completed Tasks</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <AlertCircle className="w-8 h-8 text-red-600" />
            <span className="text-3xl font-bold text-gray-900">{highPriorityCount}</span>
          </div>
          <p className="text-gray-600 font-medium">High Priority</p>
        </div>
      </div>

      {/* Tasks List */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Assigned Tasks</h2>
        {tasks.length === 0 && <p className="text-gray-600">No tasks assigned yet.</p>}
        <div className="space-y-3">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`p-4 rounded-lg border-2 transition-all ${
                task.completed
                  ? 'border-green-200 bg-green-50'
                  : task.priority === 'high'
                  ? 'border-red-200 bg-red-50'
                  : task.priority === 'medium'
                  ? 'border-yellow-200 bg-yellow-50'
                  : 'border-blue-200 bg-blue-50'
              }`}
            >
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => handleToggle(task.id)}
                  className="flex-shrink-0"
                >
                  {task.completed ? (
                    <CheckCircle2 className="w-6 h-6 text-green-600" />
                  ) : (
                    <Circle className="w-6 h-6 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
                <div className="flex-1">
                  <p className={`font-semibold ${task.completed ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                    {task.title}
                  </p>
                  {!task.completed && <p className="text-sm text-gray-600">Due: {task.dueDate}</p>}
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  task.priority === 'high' ? 'bg-red-100 text-red-700' :
                  task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-blue-100 text-blue-700'
                }`}>
                  {task.priority.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Upcoming Reminders */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Upcoming Reminders</h2>
        {upcomingReminders.length === 0 && <p className="text-gray-600">No reminders yet.</p>}
        <div className="space-y-4">
          {upcomingReminders.map((reminder, index) => (
            <div key={index} className="flex items-center space-x-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <Calendar className="w-6 h-6 text-blue-600" />
              <div className="flex-1">
                <p className="font-semibold text-gray-900">{reminder.title}</p>
                <p className="text-sm text-gray-600">{reminder.date}</p>
              </div>
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                {reminder.type}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
