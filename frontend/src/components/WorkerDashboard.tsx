import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Calendar, CheckCircle2, Lock } from 'lucide-react';
import { ComplianceBadge } from './ComplianceBadge';
import { getDomainKeyFromProc, formatDomainLabel } from './domainUtils';
import { Navigation } from './Navigation';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface WorkerDashboardProps {
  onDomainClick: (domain: string) => void;
}

interface Step {
  id: string;
  name: string;
  completed: boolean;
}

interface Procedure {
  id: string;
  templateId?: number;
  name: string;
  dueDate: string;
  status: string;
  steps: Step[];
  domain: string;
}

export function WorkerDashboard({ onDomainClick }: WorkerDashboardProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [procedures, setProcedures] = useState<{ [domain: string]: Procedure[] }>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startupId, setStartupId] = useState<string | number | null>(null);

  const handleNavigate = (page: string) => {
    if (page === 'worker-dashboard') {
      navigate('/dashboard/worker');
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Resolve startup ID: prefer user.startupId, else first active request startup
        let resolvedStartupId = (user as any)?.startupId || null;
        if (!resolvedStartupId) {
          try {
            const myRequests = await api.listMyRequests();
            const active = Array.isArray(myRequests)
              ? myRequests.filter((r: any) => (r.status || '').toLowerCase() === 'active')
              : [];
            if (active.length > 0) {
              resolvedStartupId = active[0].startup_id;
            } else {
              const approved = Array.isArray(myRequests)
                ? myRequests.filter((r: any) => (r.status || '').toLowerCase() === 'approved')
                : [];
              if (approved.length > 0) {
                resolvedStartupId = approved[0].startup_id;
              }
            }
          } catch (e) {
            console.warn('[WorkerDashboard] listMyRequests failed, falling back to all startups');
          }
        }

        if (!resolvedStartupId) {
          throw new Error('No startup associated with this worker account.');
        }

        setStartupId(resolvedStartupId);

        // Fetch procedures and normalize using embedded steps and completed_step_ids
        const procList = await api.listProcedures(resolvedStartupId);
        const withSteps: Procedure[] = (procList || []).map((proc: any) => {
          return {
            id: String(proc.id),
            name: proc.procedure_name || proc.name || 'Procedure',
            domain: getDomainKeyFromProc(proc),
            dueDate: proc.due_date || proc.deadline || 'No due date',
            status: (proc.status || 'pending').toLowerCase(),
            steps: (proc.steps || []).map((s: any) => ({
              id: String(s.id),
              name: s.name || 'Step',
              completed: (proc.completed_step_ids || []).includes(s.id)
            })),
            templateId: typeof proc.procedure_id === 'number' ? proc.procedure_id : Number(proc.procedure_id),
          } as Procedure;
        });

        const grouped = withSteps.reduce((acc: Record<string, Procedure[]>, proc: Procedure) => {
          const domainKey = proc.domain || 'other';
          acc[domainKey] = acc[domainKey] ? [...acc[domainKey], proc] : [proc];
          return acc;
        }, {});

        setProcedures(grouped);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load procedures';
        console.error('[WorkerDashboard] Load error:', msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [user]);

  const reminders = useMemo(() => {
    const items: { title: string; date: string; priority: 'high' | 'medium' | 'low'; domain: string }[] = [];
    Object.entries(procedures).forEach(([domain, domainProcedures]) => {
      domainProcedures.forEach((p) => {
        items.push({
          title: p.name,
          date: p.dueDate || 'No due date',
          domain,
          priority: 'medium'
        });
      });
    });
    return items.slice(0, 5);
  }, [procedures]);

  const toggleStep = async (domain: string, templateProcedureId: string | number, stepId: string) => {
    try {
      const domainProcedures = procedures[domain] || [];
      const targetProc = domainProcedures.find((p: any) => Number(p.templateId) === Number(templateProcedureId));
      if (!targetProc || !startupId) return;
      const targetStep = targetProc.steps.find((s) => s.id === stepId);
      if (!targetStep) return;

      const newCompleted = !targetStep.completed;
      // Compute new status based on completion after toggle
      const updatedSteps = targetProc.steps.map((s) =>
        s.id === stepId ? { ...s, completed: newCompleted } : s
      );
      const completedCount = updatedSteps.filter((s) => s.completed).length;
      const totalCount = updatedSteps.length;
      const newStatus = completedCount === totalCount
        ? 'completed'
        : completedCount > 0
          ? 'in_progress'
          : 'pending';

      await api.toggleProcedureStep(
        startupId,
        Number(templateProcedureId),
        parseInt(stepId),
        newCompleted,
        newStatus
      );

      setProcedures((prev) => ({
        ...prev,
        [domain]: (prev[domain] || []).map((proc) =>
          Number((proc as any).templateId) === Number(templateProcedureId)
            ? {
                ...proc,
                status: newStatus,
                steps: proc.steps.map((step) =>
                  step.id === stepId ? { ...step, completed: newCompleted } : step
                )
              }
            : proc
        )
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update step status';
      console.error('[WorkerDashboard] Step toggle error:', msg);
      setError(msg);
    }
  };

  const getProgress = (steps: Step[]) => {
    const completed = steps.filter(s => s.completed).length;
    return { completed, total: steps.length };
  };

  const getDomainStatus = (domain: string): 'compliant' | 'pending' | 'at-risk' => {
    const domainProcedures = procedures[domain] || [];
    const allSteps = domainProcedures.flatMap(p => p.steps);
    const completedSteps = allSteps.filter(s => s.completed).length;
    const completionRate = completedSteps / allSteps.length;

    if (completionRate === 1) return 'compliant';
    if (completionRate >= 0.5) return 'pending';
    return 'at-risk';
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-gray-600">Loading procedures...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {user && <Navigation user={user} onNavigate={handleNavigate} onLogout={logout} currentPage="worker-dashboard" />}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Worker Dashboard</h1>
        <p className="text-gray-600">View compliance procedures and track progress</p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      {/* View-Only Notice */}
      <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-4 mb-8 flex items-start space-x-3">
        <Lock className="w-5 h-5 text-blue-600 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-blue-900">Worker Access</p>
          <p className="text-sm text-blue-700">You can view and mark steps as complete, but cannot edit procedures or compliance badges.</p>
        </div>
      </div>

      {/* Compliance Overview */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Compliance Status by Domain</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.keys(procedures).map((domain) => (
            <button
              key={domain}
              onClick={() => onDomainClick(domain)}
              className="hover:scale-105 transition-transform"
            >
              <ComplianceBadge domain={domain} status={getDomainStatus(domain)} />
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Procedures List */}
        <div className="lg:col-span-2 space-y-6">
          {Object.entries(procedures).map(([domain, domainProcedures]) => (
            <div key={domain} className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900">{formatDomainLabel(domain)}</h3>
                <ComplianceBadge domain={domain} status={getDomainStatus(domain)} showLabel={false} />
              </div>
              <div className="space-y-4">
                {domainProcedures.map((procedure) => {
                  const progress = getProgress(procedure.steps);
                  const isComplete = progress.completed === progress.total;
                  const isAtRisk = progress.completed === 0;

                  return (
                    <div
                      key={procedure.id}
                      className={`border-2 rounded-lg p-4 ${
                        isComplete ? 'border-green-200 bg-green-50' :
                        isAtRisk ? 'border-red-200 bg-red-50' :
                        'border-yellow-200 bg-yellow-50'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h4 className="font-bold text-gray-900 mb-1">{procedure.name}</h4>
                          {!isComplete && <p className="text-sm text-gray-600">Due: {procedure.dueDate}</p>}
                        </div>
                        <div className="text-right">
                          <div className={`text-sm font-bold ${
                            isComplete ? 'text-green-600' :
                            isAtRisk ? 'text-red-600' :
                            'text-yellow-600'
                          }`}>
                            {progress.completed}/{progress.total}
                          </div>
                          <div className="text-xs text-gray-500">steps</div>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isComplete ? 'bg-green-500' :
                            isAtRisk ? 'bg-red-500' :
                            'bg-yellow-500'
                          }`}
                          style={{ width: `${(progress.completed / progress.total) * 100}%` }}
                        />
                      </div>

                      {/* Steps */}
                      <div className="space-y-2">
                        {procedure.steps.map((step) => (
                          <label
                            key={step.id}
                            className="flex items-center space-x-3 cursor-pointer group"
                          >
                            <input
                              type="checkbox"
                              checked={step.completed}
                              onChange={() => toggleStep(domain, (procedure as any).templateId ?? procedure.id, step.id)}
                              className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <span className={`text-sm ${step.completed ? 'text-gray-500 line-through' : 'text-gray-900 group-hover:text-blue-600'}`}>
                              {step.name}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Reminders Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Upcoming Deadlines</h3>
            <div className="space-y-3">
              {reminders.map((reminder, index) => (
                <div key={index} className={`p-4 rounded-lg border-2 ${
                  reminder.priority === 'high' ? 'border-red-200 bg-red-50' :
                  'border-yellow-200 bg-yellow-50'
                }`}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900 text-sm">{reminder.title}</p>
                      <p className="text-xs text-gray-600">{reminder.domain}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      reminder.priority === 'high' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {reminder.domain}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{reminder.date}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-6">
            <Calendar className="w-8 h-8 text-gray-400 mb-3" />
            <h3 className="text-lg font-bold text-gray-900 mb-2">Your Tasks</h3>
            <p className="text-sm text-gray-600">
              Focus on completing assigned procedure steps to help maintain compliance.
            </p>
          </div>
        </div>
      </div>
      </div>
    </>
  );
}
