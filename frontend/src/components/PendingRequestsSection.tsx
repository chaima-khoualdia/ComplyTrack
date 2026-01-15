import { useEffect, useState } from 'react';
import { UserPlus, Check, X, Copy, CheckCircle } from 'lucide-react';
import * as api from '../api';

interface PendingRequestsSectionProps {
  startupId?: string | number;
}

interface PendingRequest {
  id: string | number;
  workerName?: string;
  workerEmail?: string;
  startupName?: string;
  requestedAt?: string;
  [key: string]: any;
}

export function PendingRequestsSection({ startupId }: PendingRequestsSectionProps) {
  const [requests, setRequests] = useState<PendingRequest[]>([]);
  const [generatedCodes, setGeneratedCodes] = useState<{ [key: string]: string }>({});
  const [emailSentByReq, setEmailSentByReq] = useState<{ [key: string]: boolean }>({});
  const [resendingByReq, setResendingByReq] = useState<{ [key: string]: boolean }>({});
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        if (!startupId) {
          setRequests([]);
          return;
        }
        const result = await api.listPendingRequests(startupId);
        setRequests(Array.isArray(result) ? result : []);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Failed to load pending requests';
        console.error('[PendingRequestsSection] Load error:', msg);
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [startupId]);

  const handleApprove = async (requestId: string | number) => {
    try {
      setError(null);
      const response = await api.approveRequest(requestId);
      const code = response?.invitation_code || Math.random().toString(36).substring(2, 8).toUpperCase();
      setGeneratedCodes((prev) => ({ ...prev, [requestId]: code }));
      const sent = Boolean(response?.email_sent);
      setEmailSentByReq((prev) => ({ ...prev, [requestId]: sent }));
      if (sent) {
        setSuccess('Invitation email sent to worker');
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to approve request';
      console.error('[PendingRequestsSection] Approve error:', msg);
      setError(msg);
    }
  };

  const handleReject = async (requestId: string | number) => {
    try {
      setError(null);
      await api.rejectRequest(requestId, 'Rejected by owner');
      setRequests((prev) => prev.filter((req) => req.id !== requestId));
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to reject request';
      console.error('[PendingRequestsSection] Reject error:', msg);
      setError(msg);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  const handleResend = async (requestId: string | number) => {
    try {
      setError(null);
      setResendingByReq((prev) => ({ ...prev, [requestId]: true }));
      const resp = await api.resendInvite(requestId);
      const sent = Boolean(resp?.email_sent);
      setEmailSentByReq((prev) => ({ ...prev, [requestId]: sent }));
      if (resp?.invitation_code) {
        setGeneratedCodes((prev) => ({ ...prev, [requestId]: resp.invitation_code }));
      }
      setSuccess(sent ? 'Invitation email resent' : 'Unable to send invitation email');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to resend invite';
      console.error('[PendingRequestsSection] Resend error:', msg);
      setError(msg);
    } finally {
      setResendingByReq((prev) => ({ ...prev, [requestId]: false }));
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Pending Access Requests</h2>
        <p className="text-gray-600">Loading requests...</p>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Pending Access Requests</h2>
        {error ? (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">{error}</div>
        ) : (
          <div className="text-center py-8">
            <UserPlus className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600">No pending requests</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Pending Access Requests</h2>
        <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm font-semibold">
          {requests.length} New
        </span>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">{error}</div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>
      )}

      <div className="space-y-4">
        {requests.map((request) => {
          const workerName = request.workerName || request.worker_name || request.worker || 'Worker';
          const workerEmail = request.workerEmail || request.worker_email || request.email || 'Pending email';
          const startupName = request.startupName || request.startup_name || request.startup?.name || 'Startup';
          const requestedAt = request.requestedAt || request.requested_at || request.created_at || 'Just now';

          return (
            <div key={request.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-gray-900">{workerName}</h3>
                  <p className="text-sm text-gray-600">{workerEmail}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Requested {requestedAt} • {startupName}
                  </p>
                </div>
              </div>

              {generatedCodes[request.id] ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-green-900">Approved</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-white border border-green-300 rounded-lg px-4 py-2">
                      <p className="text-xs text-gray-600 mb-1">Invitation Code:</p>
                      <p className="text-xl font-bold text-gray-900 tracking-wider">
                        {generatedCodes[request.id]}
                      </p>
                    </div>
                    <button
                      onClick={() => handleCopyCode(generatedCodes[request.id])}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
                    >
                      {copiedCode === generatedCodes[request.id] ? (
                        <>
                          <CheckCircle className="w-4 h-4" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleResend(request.id)}
                      disabled={!!resendingByReq[String(request.id)]}
                      className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      {resendingByReq[String(request.id)] ? 'Resending…' : 'Resend Invite'}
                    </button>
                  </div>
                  {emailSentByReq[String(request.id)] && (
                    <p className="text-xs text-green-700 mt-2">Invitation email sent to {workerEmail}.</p>
                  )}
                </div>
              ) : (
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleApprove(request.id)}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Check className="w-4 h-4" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => handleReject(request.id)}
                    className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <X className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
