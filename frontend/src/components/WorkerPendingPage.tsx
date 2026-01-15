import { Clock, Building2 } from 'lucide-react';

interface WorkerPendingPageProps {
  startupName: string;
  onEnterCode: () => void;
}

export function WorkerPendingPage({ startupName, onEnterCode }: WorkerPendingPageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center">
              <Clock className="w-8 h-8 text-yellow-600" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            Waiting for Approval
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Your access request is pending review
          </p>

          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-6 mb-6">
            <div className="flex items-start space-x-3">
              <Building2 className="w-6 h-6 text-yellow-600 mt-1" />
              <div>
                <p className="font-semibold text-gray-900 mb-1">Request Details</p>
                <p className="text-sm text-gray-700">
                  Startup: <span className="font-medium">{startupName}</span>
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  The startup owner will review your request and send you an invitation code if approved.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm text-gray-600">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 font-bold">1</span>
              </div>
              <p>Request submitted successfully</p>
            </div>
            <div className="flex items-center space-x-3 text-sm text-gray-600">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-gray-600 font-bold">2</span>
              </div>
              <p>Waiting for owner approval...</p>
            </div>
            <div className="flex items-center space-x-3 text-sm text-gray-400">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-gray-400 font-bold">3</span>
              </div>
              <p>Enter invitation code</p>
            </div>
            <div className="flex items-center space-x-3 text-sm text-gray-400">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-gray-400 font-bold">4</span>
              </div>
              <p>Access dashboard</p>
            </div>
          </div>

          <div className="mt-8">
            <button
              onClick={onEnterCode}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Already Have a Code?
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
