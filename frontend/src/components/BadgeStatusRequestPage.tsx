import { useState, useEffect } from 'react';
import { Building2, Shield, CheckCircle, Clock, ArrowLeft, Loader2, ChevronDown, AlertCircle } from 'lucide-react';
import { useAuth } from '../AuthContext';
import * as api from '../api';

interface BadgeStatusRequestPageProps {
  onBack: () => void;
}

export function BadgeStatusRequestPage({ 
  onBack
}: BadgeStatusRequestPageProps) {
  const { user } = useAuth();
  const [selectedStartupId, setSelectedStartupId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [requestSent, setRequestSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolio, setPortfolio] = useState<any[]>([]);

  // Load investor portfolio on mount
  useEffect(() => {
    if (user?.id) {
      loadPortfolio();
    }
  }, [user?.id]);

  const loadPortfolio = async () => {
    try {
      setPageLoading(true);
      setError(null);
      const data = await api.getInvestorPortfolio(user!.id);
      // Map response to expected format
      const mapped = Array.isArray(data) ? data.map((item: any) => ({
        startup_id: item.startup_id,
        startup_name: item.startup_name
      })) : [];
      // Deduplicate by startup_id to avoid duplicate option keys
      const dedupedMap = new Map<number, { startup_id: number; startup_name: string }>();
      mapped.forEach((it) => {
        if (!dedupedMap.has(Number(it.startup_id))) {
          dedupedMap.set(Number(it.startup_id), {
            startup_id: Number(it.startup_id),
            startup_name: it.startup_name
          });
        }
      });
      const deduped = Array.from(dedupedMap.values());
      setPortfolio(deduped);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to load portfolio';
      setError(errMsg);
    } finally {
      setPageLoading(false);
    }
  };

  const domains = [
    { name: 'Tax', icon: '💰', description: 'Tax compliance and filings' },
    { name: 'Auditing', icon: '📊', description: 'Financial audits and reviews' },
    { name: 'Legal', icon: '⚖️', description: 'Legal documentation and contracts' },
    { name: 'Licensing', icon: '📋', description: 'Business licenses and permits' },
    { name: 'IP', icon: '💡', description: 'Intellectual property registrations' },
    { name: 'Zones', icon: '🏢', description: 'Special economic zones compliance' }
  ];

  const selectedStartup = portfolio.find(s => s.startup_id === parseInt(selectedStartupId));

  const handleRequestBadgeStatus = async () => {
    if (!selectedStartupId) return;

    try {
      setIsLoading(true);
      setError(null);
      // Create a badge status request via the backend
      await api.createBadgeStatusRequest(user!.id, parseInt(selectedStartupId));
      setRequestSent(true);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to request badge status';
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={onBack}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Portfolio
      </button>

      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <img src="/src/assets/Logo_Icon_Dark.svg" alt="ComplyTrack" className="w-8 h-8" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            Request Badge Status Update
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Get the latest compliance status for your portfolio companies
          </p>

          {pageLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : error && !requestSent ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <p className="text-sm text-red-800"><strong>Error:</strong> {error}</p>
                  <button
                    onClick={loadPortfolio}
                    className="mt-3 text-sm underline text-red-700 hover:text-red-900 font-medium"
                  >
                    Retry
                  </button>
                </div>
              </div>
            </div>
          ) : !requestSent ? (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
                <h3 className="font-semibold text-blue-900 mb-3 flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  What is Badge Status?
                </h3>
                <p className="text-blue-800 text-sm leading-relaxed">
                  Badge status provides a comprehensive compliance snapshot across all domains. 
                  Requesting a badge status update will query the startup's current compliance state 
                  in real-time and provide you with the most up-to-date information across Tax, Auditing, 
                  Legal, Licensing, IP, and Special Zones.
                </p>
              </div>

              {/* Startup Selection Dropdown */}
              <div className="mb-8">
                <label htmlFor="startup" className="block text-sm font-medium text-gray-700 mb-2">
                  Select Startup *
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 z-10" />
                  <select
                    id="startup"
                    value={selectedStartupId}
                    onChange={(e) => setSelectedStartupId(e.target.value)}
                    className="w-full pl-10 pr-10 py-4 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none bg-white text-gray-900 font-medium"
                    required
                  >
                    <option value="">-- Choose a startup --</option>
                    {portfolio.map((item, idx) => (
                      <option key={`startup-${item.startup_id}`} value={item.startup_id}>
                        {item.startup_name || `Startup ${item.startup_id}`}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                </div>
              </div>

              {selectedStartup && (
                <>
                  <div className="mb-8">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Compliance Domains to Check:</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {domains.map((domain) => (
                        <div 
                          key={domain.name}
                          className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg border border-gray-200"
                        >
                          <span className="text-2xl">{domain.icon}</span>
                          <div>
                            <h4 className="font-semibold text-gray-900">{domain.name}</h4>
                            <p className="text-sm text-gray-600">{domain.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                    <div className="flex items-start">
                      <Clock className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div>
                        <p className="text-sm text-yellow-800">
                          <strong>Note:</strong> The badge status request may take a few moments to process. 
                          We'll gather the latest compliance information from all relevant sources for{' '}
                          <strong>{selectedStartup.startup_name}</strong>.
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-6">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <button
                onClick={handleRequestBadgeStatus}
                disabled={!selectedStartupId || isLoading}
                className="w-full bg-blue-600 text-white py-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Requesting Badge Status...</span>
                  </>
                ) : (
                  <>
                    <Shield className="w-5 h-5" />
                    <span>Request Badge Status Update</span>
                  </>
                )}
              </button>
              
              {!selectedStartupId && (
                <p className="text-center text-sm text-gray-500 mt-3">
                  Please select a startup to continue
                </p>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <div className="flex justify-center mb-6">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-10 h-10 text-green-600" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                Badge Status Updated Successfully!
              </h3>
              <p className="text-gray-600 mb-8">
                The compliance badges for <strong>{selectedStartup?.startup_name}</strong> have been updated with the latest information.
              </p>
              <button
                onClick={onBack}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg"
              >
                Return to Portfolio Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

