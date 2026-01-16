// API client with JWT storage and axios + interceptors
import axios, { AxiosInstance } from 'axios';

// Prefer Vite env at build time; fallback to dev localhost
const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const TOKEN_KEY = 'jwtToken';
let currentToken: string | null = null;

// Token management
export function getToken(): string | null {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    currentToken = token;
    return token;
  } catch {
    return currentToken;
  }
}

export function setToken(token: string) {
  currentToken = token;
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // ignore storage errors
  }
}

export function clearToken() {
  currentToken = null;
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

// Axios instance with auth interceptors
const client: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' }
});

client.interceptors.request.use((config) => {
  const token = currentToken || getToken();
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      console.warn('[API] Unauthorized, clearing token');
      clearToken();
    }
    const message = error?.response?.data?.detail || error?.message || 'API error';
    return Promise.reject(new Error(message));
  }
);

// Minimal JWT payload decoder (no verification)
export function decodeJwt<T = any>(token: string): T | null {
  try {
    const [, payload] = token.split('.');
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(
      atob(normalized)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}

// Auth endpoints
export async function authLoginStep1(email: string, password: string): Promise<{ message: string }> {
  const { data } = await client.post('/auth/login-step1', { email, password });
  return data;
}

export async function authLoginStep2(email: string, otp: string): Promise<{ access_token: string; token_type: string }> {
  const { data } = await client.post('/auth/login-step2', { email, otp });
  if (data && data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

// Auth/session
export async function getMe(): Promise<any> {
  const { data } = await client.get('/auth/me');
  return data;
}

export function logout(): void {
  clearToken();
}

export async function refreshToken(): Promise<{ access_token: string; token_type: string }> {
  const { data } = await client.post('/auth/refresh');
  if (data && data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

// Registration endpoint
export async function registerUser(input: {
  email: string;
  password: string;
  role: 'owner' | 'worker' | 'investor';
  firstName: string;
  lastName: string;
}): Promise<any> {
  const { data } = await client.post('/auth/register', {
    email: input.email,
    password: input.password,
    role: input.role,
    first_name: input.firstName || 'User',
    last_name: input.lastName || 'Account'
  });
  return data;
}

// Owner: create startup
export async function createStartup(input: {
  startupName: string;
  matriculeFiscal: string;
  rneNumber: string;
  legalForm: string;
  field: string;
  sector: string;
  size: string;
  location: string;
}): Promise<any> {
  // Include founder_id from JWT token (sub)
  const token = getToken();
  const decoded = token ? decodeJwt<{ sub: number }>(token) : null;
  const founder_id = decoded?.sub;
  const { data } = await client.post('/startups', {
    founder_id,
    name: input.startupName,
    matricule_fiscal: input.matriculeFiscal,
    rne_number: input.rneNumber,
    legal_form: input.legalForm,
    field: input.field,
    sector: input.sector,
    size: input.size,
    location: input.location
  });
  return data;
}

// Worker: request access to startup
export async function createRequest(startupId: string): Promise<any> {
  const { data } = await client.post('/requests', { startup_id: startupId });
  return data;
}

// Startups and requests
export async function listMyStartups(): Promise<any> {
  // Backend has no /startups/mine; fetch all and filter client-side
  const { data } = await client.get('/startups');
  return data;
}

export async function listAllStartups(): Promise<any> {
  const { data } = await client.get('/startups');
  return data;
}

export async function listMyRequests(): Promise<any> {
  const { data } = await client.get('/requests/mine');
  return data;
}

export async function listPendingRequests(startupId: string | number): Promise<any> {
  const { data } = await client.get(`/requests/startup/${startupId}`);
  return data;
}

export async function approveRequest(requestId: string | number): Promise<any> {
  const { data } = await client.patch(`/requests/${requestId}/approve`);
  return data;
}

export async function rejectRequest(requestId: string | number, reason: string): Promise<any> {
  const { data } = await client.patch(`/requests/${requestId}/reject`, { reason });
  return data;
}

export async function resendInvite(requestId: string | number): Promise<any> {
  const { data } = await client.post(`/requests/${requestId}/resend`);
  return data;
}

// Procedures
export async function listProcedures(startupId: string | number): Promise<any> {
  const { data } = await client.get(`/startups/${startupId}/procedures`);
  return data;
}

export async function getProcedure(procedureId: string | number): Promise<any> {
  const { data } = await client.get(`/procedures/${procedureId}`);
  return data;
}

export async function createProcedure(startupId: string | number, input: any): Promise<any> {
  const { data } = await client.post(`/startups/${startupId}/procedures`, input);
  return data;
}

export async function updateProcedure(procedureId: string | number, patch: any): Promise<any> {
  const { data } = await client.patch(`/procedures/${procedureId}`, patch);
  return data;
}

export async function deleteProcedure(procedureId: string | number): Promise<any> {
  const { data } = await client.delete(`/procedures/${procedureId}`);
  return data;
}

// Steps
export async function listProcedureSteps(procedureId: string | number): Promise<any> {
  const { data } = await client.get(`/procedures/${procedureId}/steps`);
  return data;
}

// Assignments and status
export async function assignProcedure(procedureId: string | number, userId: string | number): Promise<any> {
  const { data } = await client.post(`/procedures/${procedureId}/assign`, { user_id: userId });
  return data;
}

export async function markProcedureStatus(procedureId: string | number, status: string): Promise<any> {
  const { data } = await client.post(`/procedures/${procedureId}/status`, { status });
  return data;
}

export async function toggleProcedureStep(
  startupId: string | number,
  procedureId: string | number,
  stepId: number,
  completed: boolean,
  status?: string
): Promise<any> {
  const payload: any = { step_id: stepId, completed };
  if (status) payload.status = status;
  const { data } = await client.patch(`/startups/${startupId}/procedures/${procedureId}`, payload);
  return data;
}

// Attachments
export async function uploadProcedureAttachment(procedureId: string | number, file: File | Blob): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await client.post(`/procedures/${procedureId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return data;
}

export async function listProcedureAttachments(procedureId: string | number): Promise<any> {
  const { data } = await client.get(`/procedures/${procedureId}/attachments`);
  return data;
}

export async function deleteAttachment(attachmentId: string | number): Promise<any> {
  const { data } = await client.delete(`/attachments/${attachmentId}`);
  return data;
}

// Stats endpoints
export async function getStartupStats(id: string | number): Promise<any> {
  const { data } = await client.get(`/stats/startup/${id}`);
  return data;
}

export async function getAdminStats(): Promise<any> {
  const { data } = await client.get('/stats/admin');
  return data;
}

export async function getInvestorStats(id: string | number): Promise<any> {
  const { data } = await client.get(`/stats/investor/${id}`);
  return data;
}

// Recent activity - fetch completed procedures and approved requests
export async function getRecentActivity(limit = 10): Promise<any[]> {
  try {
    const activities: any[] = [];
    
    // Fetch all startups and their completed procedures
    const startups = await listAllStartups();
    const procedureData = await Promise.all(
      startups.slice(0, 20).map(async (s: any) => {
        const procs = await listProcedures(s.id).catch(() => []);
        // Filter for completed procedures
        return procs
          .filter((p: any) => (p.status || '').toLowerCase() === 'completed')
          .map((p: any) => ({
            type: 'procedure_completed',
            startup_id: s.id,
            startup_name: s.name,
            founder_id: s.founder_id,
            procedure_name: p.procedure_name,
            completed_at: p.completed_at || p.updated_at,
            domain: p.domain
          }));
      })
    );
    activities.push(...procedureData.flat());
    
    // Optionally include request events if a backend endpoint is added
    
    // Sort by date descending and return top N
    return activities
      .sort((a: any, b: any) => {
        const aTime = Date.parse(a.completed_at || '0');
        const bTime = Date.parse(b.completed_at || '0');
        return bTime - aTime;
      })
      .slice(0, limit);
  } catch {
    return [];
  }
}

// Reminders
export async function getRemindersByStartup(startupId: string | number): Promise<any[]> {
  const { data } = await client.get(`/reminders/by-startup/${startupId}`);
  return data;
}

export async function getUpcomingReminders(startupId: string | number, daysAhead = 30): Promise<any[]> {
  const { data } = await client.get(`/reminders/upcoming/${startupId}`, {
    params: { days_ahead: daysAhead }
  });
  return data;
}

export async function getSchedulerStatus(): Promise<any> {
  const { data } = await client.get('/reminders/scheduler/status');
  return data;
}

// Admin management helpers
export async function listUsers(): Promise<any[]> {
  const { data } = await client.get('/users');
  return data;
}

export async function deleteUser(userId: string | number): Promise<any> {
  const { data } = await client.delete(`/users/${userId}`);
  return data;
}

export async function listAllReminders(): Promise<any[]> {
  const { data } = await client.get('/reminders/');
  return data;
}

export async function markReminderSent(reminderId: string | number): Promise<any> {
  const { data } = await client.patch(`/reminders/${reminderId}/mark-sent`);
  return data;
}

export async function deleteReminder(reminderId: string | number): Promise<any> {
  const { data } = await client.delete(`/reminders/${reminderId}`);
  return data;
}

export async function runSchedulerNow(): Promise<any> {
  const { data } = await client.post('/reminders/scheduler/run-now');
  return data;
}

export async function startScheduler(): Promise<any> {
  const { data } = await client.post('/reminders/scheduler/start');
  return data;
}

export async function stopScheduler(): Promise<any> {
  const { data } = await client.post('/reminders/scheduler/stop');
  return data;
}

// Admin: create user
export async function createUser(input: {
  email: string;
  password: string;
  role: 'owner' | 'worker' | 'investor' | 'admin';
  first_name: string;
  last_name: string;
}): Promise<any> {
  const { data } = await client.post('/users', input);
  return data;
}

// Admin: create startup
export async function createStartupByAdmin(input: {
  founder_id: number;
  name: string;
  matricule_fiscal: string;
  rne_number: string;
  legal_form: string;
  field: string;
  sector: string;
  size: string;
  location: string;
}): Promise<any> {
  const { data } = await client.post('/startups', input);
  return data;
}

// Badge Status Requests (Investor)
export async function createBadgeStatusRequest(investorId: number | string, startupId: number | string): Promise<any> {
  const { data } = await client.post('/investor-requests/', {
    investor_id: parseInt(String(investorId), 10),
    startup_id: parseInt(String(startupId), 10)
  });
  return data;
}

export async function getInvestorPortfolio(investorId: number): Promise<any[]> {
  const { data } = await client.get(`/investor-requests/by-investor/${investorId}`);
  // Extract portfolio companies from the response
  return data.requests || [];
}
