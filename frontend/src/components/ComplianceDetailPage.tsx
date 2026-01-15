import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import { ComplianceBadge } from './ComplianceBadge';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface ComplianceDetailPageProps {
  domain: string;
  onBack: () => void;
}

interface Step {
  id: string;
  name: string;
  completed: boolean;
  description?: string;
}

interface Procedure {
  id: string;
  name: string;
  dueDate: string;
  steps: Step[];
  domain: string;
  completedStepIds: number[];
  totalSteps: number;
}

export function ComplianceDetailPage({ domain, onBack }: ComplianceDetailPageProps) {
  const { user } = useAuth();
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startupName, setStartupName] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);

        let resolvedStartupId = (user as any)?.startupId || null;
        let resolvedStartupName = (user as any)?.startupName || '';

        if (!resolvedStartupId) {
          const mine = await api.listMyStartups();
          if (Array.isArray(mine) && mine.length > 0) {
            resolvedStartupId = mine[0].id;
            resolvedStartupName = mine[0].name || '';
          }
        }

        if (!resolvedStartupId) {
          throw new Error('No startup found for this account.');
        }

        setStartupName(resolvedStartupName || 'Startup');

        const procList = await api.listProcedures(resolvedStartupId);
        const filtered = (procList || []).filter((p: any) => (p.domain || '').toLowerCase() === domain.toLowerCase());

        const withSteps = filtered.map((proc: any) => {
          return {
            id: String(proc.id),
            name: proc.procedure_name || 'Procedure',
            domain: proc.domain || domain,
            dueDate: proc.due_date || 'No due date',
            completedStepIds: proc.completed_step_ids || [],
            totalSteps: proc.total_steps || 0,
            steps: (proc.steps || []).map((s: any) => ({
              id: String(s.id),
              name: s.name || 'Step',
              completed: (proc.completed_step_ids || []).includes(s.id),
              description: s.description || ''
            }))
          } as Procedure;
        });

        setProcedures(withSteps);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load compliance details';
        console.error('[ComplianceDetailPage] Load error:', msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [domain, user]);

  const totals = useMemo(() => {
    const totalSteps = procedures.reduce((acc, proc) => acc + proc.steps.length, 0);
    const completedSteps = procedures.reduce(
      (acc, proc) => acc + proc.steps.filter((s) => s.completed).length,
      0
    );
    return { totalSteps, completedSteps };
  }, [procedures]);

  const domainStatus: 'compliant' | 'pending' | 'at-risk' = useMemo(() => {
    if (totals.totalSteps === 0) return 'pending';
    const rate = totals.completedSteps / totals.totalSteps;
    if (rate === 1) return 'compliant';
    if (rate >= 0.5) return 'pending';
    return 'at-risk';
  }, [totals]);

  const riskLevel: 'low' | 'medium' | 'high' = useMemo(() => {
    if (totals.totalSteps === 0) return 'medium';
    const rate = totals.completedSteps / totals.totalSteps;
    if (rate >= 0.8) return 'low';
    if (rate >= 0.5) return 'medium';
    return 'high';
  }, [totals]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-gray-600">Loading compliance details...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={onBack}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </button>

      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900">{domain} Compliance</h1>
            <p className="text-gray-600">{startupName}</p>
          </div>
          <ComplianceBadge domain={domain} status={domainStatus} />
        </div>
        {error ? (
          <p className="text-red-600 text-sm">{error}</p>
        ) : (
          <p className="text-gray-600 text-lg">
            Compliance procedures and steps pulled from the backend for this domain.
          </p>
        )}
      </div>

      {/* Risk Indicator */}
      <div className={`rounded-xl p-6 mb-8 ${
        riskLevel === 'low' ? 'bg-green-50 border-2 border-green-200' :
        riskLevel === 'medium' ? 'bg-yellow-50 border-2 border-yellow-200' :
        'bg-red-50 border-2 border-red-200'
      }`}>
        <div className="flex items-center space-x-3">
          {riskLevel === 'low' ? (
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          ) : riskLevel === 'medium' ? (
            <Clock className="w-8 h-8 text-yellow-600" />
          ) : (
            <AlertCircle className="w-8 h-8 text-red-600" />
          )}
          <div>
            <h3 className={`text-xl font-bold ${
              riskLevel === 'low' ? 'text-green-900' :
              riskLevel === 'medium' ? 'text-yellow-900' :
              'text-red-900'
            }`}>
              {riskLevel === 'low' ? 'Low Risk' :
               riskLevel === 'medium' ? 'Medium Risk' :
               'High Risk - Immediate Attention Required'}
            </h3>
            <p className={`${
              riskLevel === 'low' ? 'text-green-700' :
              riskLevel === 'medium' ? 'text-yellow-700' :
              'text-red-700'
            }`}>
              {riskLevel === 'low' ? 'Most steps are complete' :
               riskLevel === 'medium' ? 'Some items need attention soon' :
               'Several items are still pending'}
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Steps */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Compliance Requirements</h2>
        {procedures.length === 0 && (
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-gray-700">
            No procedures found for this domain yet.
          </div>
        )}
        <div className="space-y-4">
          {procedures.map((procedure) => (
            <div key={procedure.id} className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{procedure.name}</h3>
                  <p className="text-sm text-gray-600">Due: {procedure.dueDate}</p>
                </div>
                <span className="text-sm text-gray-500">{procedure.steps.length} steps</span>
              </div>

              {procedure.steps.map((step) => (
                <div
                  key={step.id}
                  className={`p-4 rounded-lg border-2 ${
                    step.completed ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {step.completed ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600 mt-1" />
                      ) : (
                        <Clock className="w-5 h-5 text-yellow-600 mt-1" />
                      )}
                      <div>
                        <p className={`font-semibold ${
                          step.completed ? 'text-green-900' : 'text-yellow-900'
                        }`}>
                          {step.name}
                        </p>
                        <p className="text-sm text-gray-600">{step.description || 'Step details not provided'}</p>
                      </div>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${
                      step.completed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {step.completed ? 'Complete' : 'Pending'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
