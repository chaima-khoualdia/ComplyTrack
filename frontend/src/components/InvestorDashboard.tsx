import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, CheckCircle, AlertTriangle, Plus } from 'lucide-react';
import { ComplianceBadge } from './ComplianceBadge';
import { Navigation } from './Navigation';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import * as api from '../api';
import { useAuth } from '../AuthContext';

interface InvestorDashboardProps {
  onDomainClick?: (domain: string) => void;
}

interface InvestorStats {
  investor_id: number;
  portfolio_status: {compliant: number; pending: number; at_risk: number};
  compliance_by_domain: Array<{domain: string; compliance_rate: number}>;
  portfolio_companies: number[];
  overall_compliance_rate: number;
  companies_need_attention: number;
}

export function InvestorDashboard({ onDomainClick }: InvestorDashboardProps) {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<'all' | 'compliant' | 'pending' | 'at-risk'>('all');
  const [stats, setStats] = useState<InvestorStats | null>(null);
  const [portfolio, setPortfolio] = useState<any[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, logout } = useAuth();

  const handleNavigate = (page: string) => {
    if (page === 'investor-dashboard') {
      navigate('/dashboard/investor');
    } else if (page === 'badge-status-request') {
      navigate('/badge-status-request');
    }
  };

  useEffect(() => {
    fetchInvestorData();
  }, []);

  const fetchInvestorData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      if (!user?.id) {
        throw new Error('Missing authenticated user. Please log in again.');
      }
      const statsResp = await api.getInvestorStats(user.id);
      console.log('[InvestorDashboard] Fetched stats:', statsResp);
      setStats(statsResp);
      setPortfolio(statsResp?.portfolio_companies || []);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load investor stats';
      console.error('[InvestorDashboard] Error:', errorMsg);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-gray-600">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
          <button onClick={fetchInvestorData} className="ml-2 underline font-semibold">
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Transform backend data to match component expectations
  const startupsFromStats = stats?.portfolio_status ? Object.entries(stats.portfolio_status).map(([name, data]: [string, any], idx) => ({
    id: idx + 1,
    name: name,
    compliance: data.domains || {}
  })) : [];

  const startupsFromPortfolio = Array.isArray(portfolio)
    ? portfolio.map((item: any, idx: number) => ({
        id: item.id || idx + 1,
        name: item.name || item.startup_name || `Startup ${idx + 1}`,
        compliance: item.compliance || item.domains || item.status_by_domain || {}
      }))
    : [];

  const startups = startupsFromPortfolio.length ? startupsFromPortfolio : startupsFromStats;

  const getOverallStatus = (compliance: any) => {
    const statuses = Object.values(compliance);
    if (statuses.includes('at-risk')) return 'at-risk';
    if (statuses.includes('pending')) return 'pending';
    return 'compliant';
  };

  const filteredStartups = startups.filter(startup => {
    if (filter === 'all') return true;
    return getOverallStatus(startup.compliance) === filter;
  });

  // Chart data - dynamically derived from backend stats
  const domainAbbreviations: Record<string, string> = {
    legal_registration: 'Legal',
    tax_compliance: 'Tax',
    tech_ip_compliance: 'Tech/IP',
    licensing: 'Lic.',
    auditing_reporting: 'Audit',
    special_zones: 'Zones',
    startup_incentives: 'Incentives',
  };

  const domainDistribution = (() => {
    const map: Record<string, { domain: string; domainKey: string; compliant: number; pending: number; at_risk: number; total: number }> = {};
    startups.forEach(s => {
      const comp = s.compliance || {};
      Object.entries(comp).forEach(([rawDomain, status]) => {
        const key = String(rawDomain);
        const label = domainAbbreviations[key] || key;
        if (!map[label]) {
          map[label] = { domain: label, domainKey: key, compliant: 0, pending: 0, at_risk: 0, total: 0 };
        }
        if (status === 'compliant') map[label].compliant += 1;
        else if (status === 'pending') map[label].pending += 1;
        else if (status === 'at-risk' || status === 'at_risk') map[label].at_risk += 1;
        map[label].total += 1;
      });
    });
    return Object.values(map);
  })();

  // Overall distribution - derive from stats if available
  const totalCompanies = startups.length;
  const ps = stats?.portfolio_status || { compliant: 0, pending: 0, at_risk: 0 };
  const overallData = [
    { name: 'Compliant', value: (ps.compliant || 0) * totalCompanies, color: '#10b981' },
    { name: 'Pending', value: (ps.pending || 0) * totalCompanies, color: '#f59e0b' },
    { name: 'At Risk', value: (ps.at_risk || 0) * totalCompanies, color: '#ef4444' }
  ];
  const overallDataNonZero = overallData.filter((d) => d.value > 0);
  const overallRate = stats?.overall_compliance_rate ?? 0;
  const attentionCount = stats?.companies_need_attention ?? 0;

  return (
    <>
      {user && <Navigation user={user} onNavigate={handleNavigate} onLogout={logout} currentPage="investor-dashboard" />}
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Portfolio Compliance Overview</h1>
            <p className="text-gray-600">Monitor compliance status across your investments</p>
          </div>
          <button
            onClick={() => handleNavigate('badge-status-request')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg flex items-center space-x-2"
          >
            <Plus className="w-5 h-5" />
            <span>Request Badge Status</span>
          </button>
        </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <Building2 className="w-8 h-8 text-blue-600" />
            <span className="text-3xl font-bold text-gray-900">{totalCompanies}</span>
          </div>
          <p className="text-gray-600 font-medium">Portfolio Companies</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <span className="text-3xl font-bold text-gray-900">{(overallRate <= 1 ? Math.round(overallRate * 100) : Math.round(overallRate))}%</span>
          </div>
          <p className="text-gray-600 font-medium">Overall Compliance Rate</p>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="w-8 h-8 text-yellow-600" />
            <span className="text-3xl font-bold text-gray-900">{attentionCount}</span>
          </div>
          <p className="text-gray-600 font-medium">Companies Need Attention</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Compliance by Domain</h2>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={domainDistribution} barCategoryGap="25%" barGap={2} margin={{ top: 8, right: 16, left: 8, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="domain"
                type="category"
                interval={0}
                tickLine={false}
                axisLine={{ stroke: '#e5e7eb' }}
                tick={{ fontSize: 11, textAnchor: 'end' }}
                height={80}
                padding={{ left: 20, right: 20 }}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="compliant" fill="#10b981" name="Compliant" />
              <Bar dataKey="pending" fill="#f59e0b" name="Pending" />
              <Bar dataKey="at_risk" fill="#ef4444" name="At Risk" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Overall Portfolio Status</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={overallDataNonZero}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {overallDataNonZero.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex space-x-2 mb-6">
        {(['all', 'compliant', 'pending', 'at-risk'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === status
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {status.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
          </button>
        ))}
      </div>

      {/* Startups List */}
      <div className="space-y-4">
        {filteredStartups.map((startup) => (
          <div key={startup.id} className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{startup.name}</h3>
              </div>
              <div className={`px-4 py-2 rounded-full font-semibold ${
                getOverallStatus(startup.compliance) === 'compliant' ? 'bg-green-100 text-green-700' :
                getOverallStatus(startup.compliance) === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              }`}>
                {getOverallStatus(startup.compliance).split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(startup.compliance).map(([domain, status]) => (
                <button
                  key={domain}
                  onClick={() => onDomainClick ? onDomainClick(domain) : undefined}
                  className="hover:scale-105 transition-transform"
                >
                  <ComplianceBadge domain={domain} status={status as any} />
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      </div>
    </>
  );
}