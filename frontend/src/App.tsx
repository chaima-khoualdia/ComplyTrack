import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import { useEffect, useState } from 'react';
import { decodeJwt, getToken, listMyStartups } from './api';
import { ProtectedRoute } from './ProtectedRoute';
import { LandingPage } from './components/LandingPage';
import { LoginPage } from './components/LoginPage';
import { OTPVerification } from './components/OTPVerification';
import { PublicRegistrationPage } from './components/PublicRegistrationPage';
import { StartupRegistrationPage } from './components/StartupRegistrationPage';
import { WorkerRequestAccessPage } from './components/WorkerRequestAccessPage';
import { WorkerPendingPage } from './components/WorkerPendingPage';
import { WorkerInvitationCodePage } from './components/WorkerInvitationCodePage';
import { AdminDashboard } from './components/AdminDashboard';
import { InvestorDashboard } from './components/InvestorDashboard';
import { BadgeStatusRequestPage } from './components/BadgeStatusRequestPage';
import { StartupOwnerDashboard } from './components/StartupOwnerDashboard';
import { WorkerDashboard } from './components/WorkerDashboard';
import { ComplianceDetailPage } from './components/ComplianceDetailPage';
import { RemindersPage } from './components/RemindersPage';
import { UserCreationPage } from './components/UserCreationPage';
import { StartupCreationPage } from './components/StartupCreationPage';
import { AdminManagementPage } from './components/AdminManagementPage';

// Role-based redirect component
function RoleBasedRedirect() {
  const { user, isAuthenticated, initialized } = useAuth();
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    async function resolveTarget() {
      if (!isAuthenticated || !user) {
        setTarget('/login');
        return;
      }

      if (user.role === 'owner') {
        try {
          const token = getToken();
          const decoded = token ? decodeJwt<{ sub: number }>(token) : null;
          const uid = decoded?.sub;
          const startups = await listMyStartups();
          const owned = Array.isArray(startups)
            ? startups.filter((s: any) => String(s.founder_id) === String(uid))
            : [];
          if (owned.length === 0) {
            setTarget('/startup-registration');
            return;
          }
        } catch {
          setTarget('/startup-registration');
          return;
        }
      }

      const dashboardMap: Record<string, string> = {
        admin: '/dashboard/admin',
        investor: '/dashboard/investor',
        owner: '/dashboard/owner',
        worker: '/dashboard/worker'
      };
      const path = user ? dashboardMap[user.role] : '/dashboard/worker';
      setTarget(path);
    }

    if (initialized) {
      resolveTarget();
    }
  }, [initialized, isAuthenticated, user]);

  if (!initialized || !target) {
    return null;
  }

  return <Navigate to={target} replace />;
}


function AppContent() {
  const AdminManagementRoute = () => {
    const navigate = useNavigate();
    return (
      <ProtectedRoute requiredRoles={['admin']}>
        <AdminManagementPage
          onBack={() => navigate('/dashboard/admin')}
          onCreateUser={() => navigate('/admin/create-user')}
          onCreateStartup={() => navigate('/admin/create-startup')}
          onNavigate={(page) => navigate(page)}
        />
      </ProtectedRoute>
    );
  };
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/otp" element={<OTPVerification />} />
      <Route path="/register" element={<PublicRegistrationPage />} />

      {/* Protected routes */}
      <Route
        path="/startup-registration"
        element={
          <ProtectedRoute requiredRoles={['owner']}>
            <StartupRegistrationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/worker-request-access"
        element={
          <ProtectedRoute requiredRoles={['worker']}>
            <WorkerRequestAccessPage onSubmit={() => {}} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/worker-pending"
        element={
          <ProtectedRoute requiredRoles={['worker']}>
            <WorkerPendingPage startupName="TechStart Inc." onEnterCode={() => {}} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/worker-code-entry"
        element={
          <ProtectedRoute requiredRoles={['worker']}>
            <WorkerInvitationCodePage onVerify={() => {}} onBack={() => {}} />
          </ProtectedRoute>
        }
      />

      {/* Dashboard routes */}
      <Route
        path="/dashboard/admin"
        element={
          <ProtectedRoute requiredRoles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/investor"
        element={
          <ProtectedRoute requiredRoles={['investor']}>
            <InvestorDashboard onDomainClick={() => {}} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/badge-status-request"
        element={
          <ProtectedRoute requiredRoles={['investor']}>
            <BadgeStatusRequestPage onBack={() => window.history.back()} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/owner"
        element={
          <ProtectedRoute requiredRoles={['owner']}>
            <StartupOwnerDashboard onDomainClick={() => {}} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/worker"
        element={
          <ProtectedRoute requiredRoles={['worker']}>
            <WorkerDashboard onDomainClick={() => {}} />
          </ProtectedRoute>
        }
      />

      {/* Compliance detail page */}
      <Route
        path="/compliance-detail/:domain"
        element={
          <ProtectedRoute>
            <ComplianceDetailPage domain="Tax" onBack={() => {}} />
          </ProtectedRoute>
        }
      />

      {/* Reminders */}
      <Route
        path="/reminders"
        element={
          <ProtectedRoute>
            <RemindersPage />
          </ProtectedRoute>
        }
      />

      {/* Admin: Create User */}
      <Route
        path="/admin/create-user"
        element={
          <ProtectedRoute requiredRoles={['admin']}>
            <UserCreationPage />
          </ProtectedRoute>
        }
      />

      {/* Admin: Create Startup */}
      <Route
        path="/admin/create-startup"
        element={
          <ProtectedRoute requiredRoles={['admin']}>
            <StartupCreationPage />
          </ProtectedRoute>
        }
      />

      {/* Admin: Management Page */}
      <Route path="/admin/management" element={<AdminManagementRoute />} />

      {/* Catch-all - redirect authenticated users to dashboard, others to login */}
      <Route path="/*" element={<RoleBasedRedirect />} />
    </Routes>
  );
}


export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}