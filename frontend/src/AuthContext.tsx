import React, { createContext, useContext, useState, useEffect } from 'react';
import * as api from './api';

export type UserRole = 'admin' | 'investor' | 'owner' | 'worker';

export interface AuthUser {
  id: string;
  email: string;
  role: UserRole;
  name: string;
  startupId?: string;
  startupName?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  error: string | null;
  loginEmail: string;
  token: string | null;
  initialized: boolean;
  isAuthenticated: boolean;
  setLoginEmail: (email: string) => void;
  setError: (error: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  verifyOtp: (otp: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    role: UserRole;
    firstName: string;
    lastName: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loginEmail, setLoginEmail] = useState('');
  const [token, setTokenState] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Check for existing token on mount
  useEffect(() => {
    const stored = api.getToken();
    if (stored) {
      setTokenState(stored);
      const decoded = api.decodeJwt<{ sub: number; role: string }>(stored);
      if (decoded) {
        setUser({
          id: String(decoded.sub),
          email: '',
          role: (decoded.role as UserRole) || 'worker',
          name: 'User'
        });
      }
    }
    setInitialized(true);
  }, []);

  const login = async (email: string, password: string) => {
    console.log('[Auth] Logging in...');
    setIsLoading(true);
    setError(null);
    try {
      await api.authLoginStep1(email, password);
      setLoginEmail(email);
      console.log('[Auth] OTP sent to', email);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      console.error('[Auth] Login error:', msg);
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const verifyOtp = async (otp: string) => {
    console.log('[Auth] Verifying OTP...');
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.authLoginStep2(loginEmail, otp);
      if (response?.access_token) {
        setTokenState(response.access_token);
        const decoded = api.decodeJwt<{ sub: number; role: string }>(response.access_token);
        if (decoded) {
          setUser({
            id: String(decoded.sub),
            email: loginEmail,
            role: (decoded.role as UserRole) || 'worker',
            name: 'User'
          });
        }
      }
      console.log('[Auth] OTP verified successfully');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'OTP verification failed';
      console.error('[Auth] OTP error:', msg);
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
      setInitialized(true);
    }
  };

  const register = async (data: {
    email: string;
    password: string;
    role: UserRole;
    firstName: string;
    lastName: string;
  }) => {
    console.log('[Auth] Registering user...');
    setIsLoading(true);
    setError(null);
    try {
      // Only owner, worker, investor can register via API
      if (data.role === 'admin') {
        throw new Error('Admin registration is not allowed through public registration');
      }
      await api.registerUser({
        ...data,
        role: data.role as 'owner' | 'worker' | 'investor'
      });
      console.log('[Auth] Registration successful');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed';
      console.error('[Auth] Registration error:', msg);
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    console.log('[Auth] Logging out...');
    api.clearToken();
    setUser(null);
    setLoginEmail('');
    setTokenState(null);
    setError(null);
    setInitialized(true);
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ user, isLoading, error, loginEmail, token, initialized, isAuthenticated, setLoginEmail, setError, login, verifyOtp, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
