import { api } from './client';
import type { Holiday, HolidayDetail, HolidaySummary } from '@/types/api';

export interface HolidayInput {
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  destinations?: { city: string; iata?: string | null; country?: string | null }[];
  notes?: string | null;
  currency?: string;
}

export const holidaysApi = {
  list: () => api.get<HolidaySummary[]>('/api/holidays'),
  get: (id: number) => api.get<HolidayDetail>(`/api/holidays/${id}`),
  create: (body: HolidayInput) => api.post<Holiday>('/api/holidays', body),
  update: (id: number, body: Partial<HolidayInput>) =>
    api.patch<Holiday>(`/api/holidays/${id}`, body),
  remove: (id: number) => api.delete<void>(`/api/holidays/${id}`),
};
