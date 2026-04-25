import { api } from './client';
import type { FlightEntry, PriceSnapshot } from '@/types/api';

export interface FlightInput {
  origin_iata: string;
  destination_iata: string;
  depart_date: string;
  return_date?: string | null;
  airline_code?: string | null;
  airline_name?: string | null;
  cabin?: string | null;
  passengers?: number;
  source_url?: string | null;
  initial_price: string;
  currency?: string;
  tracking_enabled?: boolean;
}

const base = (holidayId: number) => `/api/holidays/${holidayId}/flights`;

export const flightsApi = {
  list: (holidayId: number) => api.get<FlightEntry[]>(base(holidayId)),
  create: (holidayId: number, body: FlightInput) =>
    api.post<FlightEntry>(base(holidayId), body),
  get: (holidayId: number, id: number) =>
    api.get<FlightEntry>(`${base(holidayId)}/${id}`),
  update: (holidayId: number, id: number, body: Partial<FlightInput> & { tracking_enabled?: boolean; archived?: boolean }) =>
    api.patch<FlightEntry>(`${base(holidayId)}/${id}`, body),
  remove: (holidayId: number, id: number) =>
    api.delete<void>(`${base(holidayId)}/${id}`),
  snapshots: (holidayId: number, id: number) =>
    api.get<PriceSnapshot[]>(`${base(holidayId)}/${id}/snapshots`),
  refresh: (holidayId: number, id: number, body: { price: string; currency?: string }) =>
    api.post<PriceSnapshot>(`${base(holidayId)}/${id}/refresh`, body),
};
