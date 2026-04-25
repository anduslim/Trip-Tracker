import { api } from './client';

export interface ShareToken {
  token: string;
  url: string;
  revoked_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface PublicShareData {
  holiday: {
    name: string;
    start_date: string | null;
    end_date: string | null;
    destinations: { city: string; iata?: string | null; country?: string | null }[];
    currency: string;
  };
  flight_entries: {
    id: number;
    origin_iata: string;
    destination_iata: string;
    depart_date: string;
    return_date: string | null;
    airline_name: string | null;
    cabin: string | null;
    passengers: number;
    initial_price: string;
    latest_price: string;
    currency: string;
    snapshots: { price: string; currency: string; captured_at: string }[];
  }[];
  comparison: ComparisonResponse;
}

export interface ComparisonResponse {
  route_groups: {
    origin: string;
    destination: string;
    entry_count: number;
    min_price: string;
    avg_price: string;
    max_price: string;
    cheapest_entry_id: number;
  }[];
  insights: {
    cheapest_route: {
      origin: string;
      destination: string;
      price: string;
      currency: string;
      flight_entry_id: number;
    } | null;
    biggest_drop_30d: {
      flight_entry_id: number;
      origin: string;
      destination: string;
      delta: string;
      delta_pct: number;
      currency: string;
    } | null;
    avg_price_per_route: {
      origin: string;
      destination: string;
      avg_price: string;
      entry_count: number;
    }[];
  };
}

export const shareApi = {
  get: (holidayId: number) => api.get<ShareToken | null>(`/api/holidays/${holidayId}/share`),
  create: (holidayId: number) => api.post<ShareToken>(`/api/holidays/${holidayId}/share`),
  revoke: (holidayId: number) => api.delete<void>(`/api/holidays/${holidayId}/share`),
  publicShare: (token: string) => api.get<PublicShareData>(`/api/public/share/${token}`),
  comparison: (holidayId: number) =>
    api.get<ComparisonResponse>(`/api/holidays/${holidayId}/flights/comparison`),
};
