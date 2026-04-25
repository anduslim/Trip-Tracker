import { api } from './client';
import type { User } from '@/types/api';

export const authApi = {
  me: () => api.get<User>('/api/auth/me'),
  register: (body: { email: string; password: string; display_name?: string }) =>
    api.post<User>('/api/auth/register', body),
  login: (body: { email: string; password: string }) =>
    api.post<User>('/api/auth/login', body),
  logout: () => api.post<void>('/api/auth/logout'),
};
