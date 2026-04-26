import { api } from './client';
import type { FlightEntry } from '@/types/api';

export interface SearchOffer {
  provider: string;
  provider_offer_id: string;
  origin_iata: string;
  destination_iata: string;
  depart_date: string;
  return_date: string | null;
  airline_code: string | null;
  airline_name: string | null;
  cabin: string | null;
  passengers: number;
  price: string;
  currency: string;
  deep_link: string | null;
}

export interface SearchResponse {
  provider: string;
  offers: SearchOffer[];
}

export interface SearchInput {
  origin: string;
  destination: string;
  depart_date: string;
  return_date?: string | null;
  passengers?: number;
  cabin?: string | null;
  currency?: string;
  max_price?: string | null;
  max_results?: number;
  provider?: string | null;
  min_duration_days?: number | null;
  max_duration_days?: number | null;
}

export const searchApi = {
  providers: () => api.get<{ providers: string[] }>('/api/search/providers'),
  flights: (body: SearchInput) => api.post<SearchResponse>('/api/search/flights', body),
  saveOffer: (body: { holiday_id: number; offer: SearchOffer }) =>
    api.post<FlightEntry>('/api/search/save-offer', body),
};
