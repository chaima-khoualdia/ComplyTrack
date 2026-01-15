import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Send } from 'lucide-react';
import * as api from '../api';

interface WorkerRequestAccessPageProps {
  onSubmit?: (startupId: string) => void;
}

interface Startup {
  id: number;
  name: string;
}

export function WorkerRequestAccessPage({ onSubmit }: WorkerRequestAccessPageProps) {
  const [selectedStartup, setSelectedStartup] = useState('');
  const [startups, setStartups] = useState<Startup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStartups();
  }, []);

  const fetchStartups = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await api.listAllStartups();
      setStartups(Array.isArray(result) ? result : []);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load startups';
      console.error('[WorkerRequestAccessPage] Error:', errorMsg);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStartup) return;

    setIsSubmitting(true);
    setError(null);
    
    try {
      // Call backend API to create request
      await api.createRequest(selectedStartup);
      
      if (onSubmit) {
        onSubmit(selectedStartup);
      } else {
        // Navigate to pending page or dashboard
        navigate('/worker-pending');
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to request access';
      console.error('[WorkerRequestAccessPage] Error:', errorMsg);
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
              <Building2 className="w-8 h-8 text-purple-600" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            Request Access
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Select a startup to join and request access
          </p>

          {isLoading && <p className="text-center text-gray-600">Loading startups...</p>}

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          {!isLoading && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="startup" className="block text-sm font-medium text-gray-700 mb-2">
                Select Startup *
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <select
                  id="startup"
                  value={selectedStartup}
                  onChange={(e) => setSelectedStartup(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all appearance-none bg-white"
                  required
                >
                  <option value="">Choose a startup...</option>
                  {startups.map((startup) => (
                    <option key={startup.id} value={startup.id}>
                      {startup.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Your request will be sent to the startup owner for approval. 
                You'll receive an invitation code once approved.
              </p>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
              <span>{isSubmitting ? 'Sending...' : 'Send Request'}</span>
            </button>
          </form>
          )}
        </div>
      </div>
    </div>
  );
}
