import { useState, useRef, KeyboardEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '../AuthContext';
import { decodeJwt, getToken, listMyStartups } from '../api';

interface OTPVerificationProps {
  onVerify?: (otp: string) => void;
  onBack?: () => void;
}

export function OTPVerification({ onVerify, onBack }: OTPVerificationProps) {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const { verifyOtp, isLoading, error, user } = useAuth();
  const navigate = useNavigate();

  const handleChange = (index: number, value: string) => {
    if (value.length > 1) return;
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const otpString = otp.join('');
    if (otpString.length === 6) {
      try {
        await verifyOtp(otpString);
        // Post-verify: derive role and id from the freshly stored token
        const token = getToken();
        const decoded = token ? decodeJwt<{ sub: number; role: string }>(token) : null;
        const resolvedRole = (decoded?.role || user?.role || 'worker') as 'admin' | 'investor' | 'owner' | 'worker';
        const resolvedUserId = decoded?.sub;

        if (resolvedRole === 'owner' && resolvedUserId) {
          // Check if owner already has a startup; if not, go to registration
          try {
            const startups = await listMyStartups();
            const owned = Array.isArray(startups)
              ? startups.filter((s: any) => String(s.founder_id) === String(resolvedUserId))
              : [];
            if (owned.length === 0) {
              navigate('/startup-registration');
              return;
            }
          } catch {
            // On failure, default to registration for safety
            navigate('/startup-registration');
            return;
          }
        }

        const map: Record<string, string> = {
          admin: '/dashboard/admin',
          investor: '/dashboard/investor',
          owner: '/dashboard/owner',
          worker: '/dashboard/worker'
        };
        navigate(map[resolvedRole] || '/dashboard/worker');
      } catch (err) {
        console.error('OTP verification failed:', err);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <button
          onClick={() => onBack ? onBack() : navigate('/login')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Login
        </button>

        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <img src="/src/assets/Logo_Icon_Dark.svg" alt="ComplyTrack" className="w-8 h-8" />
            </div>
          </div>

          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            Verify Your Identity
          </h2>
          <p className="text-center text-gray-600 mb-8">
            Enter the 6-digit code sent to your email
          </p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="flex justify-center gap-3 mb-8">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => { inputRefs.current[index] = el; }}
                  type="text"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className="w-12 h-14 text-center text-2xl font-semibold border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  required
                />
              ))}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verifying...' : 'Verify & Access Dashboard'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
              Resend Code
            </button>
          </div>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>For demo: enter any 6-digit code</p>
          </div>
        </div>
      </div>
    </div>
  );
}
