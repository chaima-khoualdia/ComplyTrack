import { useEffect, useState } from 'react';
import { AlertCircle, Calendar, CheckCircle2 } from 'lucide-react';
import { ComplianceBadge } from './ComplianceBadge';
import { formatDomainLabel, getDomainKeyFromProc } from './domainUtils';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface StartupDashboardProps {
  onDomainClick: (domain: string) => void;
}

export function StartupDashboard({ onDomainClick }: StartupDashboardProps) {
  const { user } = useAuth();
  const [startupId, setStartupId] = useState<string | number | null>(null);
  const [procedures, setProcedures] = useState<Record<string, any[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Resolve startup ID: prefer user.startupId, else first from listMyStartups
        let resolvedStartupId = (user as any)?.startupId || null;
        if (!resolvedStartupId) {
          const myStartups = await api.listMyStartups();
          if (Array.isArray(myStartups) && myStartups.length > 0) {
            resolvedStartupId = myStartups[0].id;
          }
        }
        if (!resolvedStartupId) {
          throw new Error('No startup associated with this account.');
        }
        setStartupId(resolvedStartupId);

        // Fetch stats and procedures
        const [statsResp, proceduresResp] = await Promise.all([
          api.getStartupStats(resolvedStartupId),
          api.listProcedures(resolvedStartupId)
        ]);
        setStats(statsResp);

        const domainGrouped = (proceduresResp || []).reduce((acc: Record<string, any[]>, proc: any) => {
          const domain = getDomainKeyFromProc(proc);
          const status = (proc.status || proc.compliance_status || '').toLowerCase();
          acc[domain] = acc[domain] || [];
          acc[domain].push({
            id: proc.id,
            name: proc.procedure_name || proc.name || 'Procedure',
            status: status || 'pending',
            dueDate: proc.due_date || proc.deadline || 'No due date'
          });
          return acc;
        }, {});

        setProcedures(domainGrouped);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load startup data';
        console.error('[StartupDashboard] Load error:', msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [user]);

  const getDomainStatus = (domainProcedures: any[]) => {
    const statuses = domainProcedures.map(p => (p.status || '').toLowerCase());
    if (statuses.includes('at-risk')) return 'at-risk';
    if (statuses.includes('pending')) return 'pending';
    return 'compliant';
  };

  const complianceDomains = Object.entries(procedures).map(([domain, procs]) => ({
    domain,
    status: getDomainStatus(procs),
    procedures: procs
  }));

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'text-green-600';
      case 'pending':
        return 'text-yellow-600';
      case 'at-risk':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Compliance Dashboard</h1>
        <p className="text-gray-600">Track and manage your compliance procedures</p>
      </div>

      {isLoading && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700">
          Loading startup data...
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      {/* Compliance Overview */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Compliance Status by Domain</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {complianceDomains.map((item) => (
            <button
              key={item.domain}
              onClick={() => onDomainClick(item.domain)}
              className="hover:scale-105 transition-transform"
            >
              <ComplianceBadge domain={item.domain} status={item.status as 'compliant' | 'pending' | 'at-risk'} />
            </button>
          ))}
        </div>
      </div>

      {/* Compliance Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {complianceDomains.map((domain) => (
          <div key={domain.domain} className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-gray-900">{domain.domain}</h3>
              <ComplianceBadge domain={domain.domain} status={domain.status as 'compliant' | 'pending' | 'at-risk'} showLabel={false} />
            </div>
            <div className="space-y-3">
              {domain.procedures.map((procedure, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-2 ${
                    procedure.status === 'complete' ? 'border-green-200 bg-green-50' :
                    procedure.status === 'pending' ? 'border-yellow-200 bg-yellow-50' :
                    'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {procedure.status === 'complete' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5" />
                      ) : procedure.status === 'at-risk' ? (
                        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                      ) : (
                        <Calendar className="w-5 h-5 text-yellow-600 mt-0.5" />
                      )}
                      <div>
                        <p className={`font-semibold ${getStatusColor(procedure.status)}`}>
                          {procedure.name}
                        </p>
                        <p className="text-sm text-gray-600">{procedure.dueDate}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}