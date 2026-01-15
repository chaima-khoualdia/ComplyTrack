import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth, UserRole } from './AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: UserRole[];
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const { user, isAuthenticated, initialized } = useAuth();

  // Wait for auth restoration on initial load
  if (!initialized) {
    return null;
  }

  // If no valid token, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Enforce role checks only when user is loaded
  if (requiredRoles && user && !requiredRoles.includes(user.role)) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
