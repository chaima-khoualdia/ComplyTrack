import { useNavigate } from 'react-router-dom';
import { Shield, Users, Bell, BarChart3, Lock, CheckCircle } from 'lucide-react';

interface LandingPageProps {
  onNavigate?: () => void;
  onRegister?: () => void;
}

export function LandingPage({ onNavigate, onRegister }: LandingPageProps) {
  const navigate = useNavigate();

  const features = [
    {
      icon: Lock,
      title: 'Secure Authentication',
      description: 'JWT-based authentication with OTP verification for enhanced security.'
    },
    {
      icon: CheckCircle,
      title: 'Compliance Tracking',
      description: 'Track compliance across Tax, Legal, Auditing, Licensing, IP, and Special Zones.'
    },
    {
      icon: Bell,
      title: 'Smart Reminders',
      description: 'Automated daily email reminders at 9:00 AM for upcoming deadlines.'
    },
    {
      icon: BarChart3,
      title: 'Visual Dashboards',
      description: 'Role-based dashboards with real-time compliance status and risk indicators.'
    },
    {
      icon: Users,
      title: 'Multi-Role Access',
      description: 'Tailored experiences for admins, investors, startups, and team members.'
    },
    {
      icon: Shield,
      title: 'Risk Management',
      description: 'Color-coded risk indicators to quickly identify compliance gaps.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <img 
              src="/src/assets/Logo_Full_Dark_Large.svg" 
              alt="ComplyTrack" 
              className="h-20 w-auto"
            />
          </div>
          
          <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
            A comprehensive platform for managing legal compliance across Tax, Auditing, Legal, Licensing, IP, and Special Zones — designed for investors, startups, and compliance teams.
          </p>
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => onNavigate ? onNavigate() : navigate('/login')}
              className="bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
            >
              Login to Your Dashboard
            </button>
            <button
              onClick={() => onRegister ? onRegister() : navigate('/register')}
              className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-50 transition-colors shadow-lg hover:shadow-xl"
            >
              Create Account
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="bg-white p-8 rounded-xl shadow-md hover:shadow-lg transition-shadow border border-gray-100"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* Stats Section */}
        <div className="mt-24 bg-white rounded-2xl shadow-xl p-12">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Built for Scale
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">100%</div>
              <div className="text-gray-600">Compliance Coverage</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">24/7</div>
              <div className="text-gray-600">Monitoring</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-indigo-600 mb-2">Real-time</div>
              <div className="text-gray-600">Updates</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 mb-2">Multi-role</div>
              <div className="text-gray-600">Access Control</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
