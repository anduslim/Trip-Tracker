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
  price_rating: 'cheap' | 'good' | 'typical' | 'expensive' | null;
}

export interface PriceAnalysisDto {
  origin_iata: string;
  destination_iata: string;
  depart_date: string;
  currency: string;
  minimum: string;
  first: string;
  median: string;
  third: string;
  maximum: string;
}

export interface SearchResponse {
  provider: string;
  offers: SearchOffer[];
  price_analysis: PriceAnalysisDto | null;
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

export interface MultiLegInput {
  legs: { origin: string; destination: string; depart_date: string }[];
  passengers?: number;
  cabin?: string | null;
  currency?: string;
  max_price_per_leg?: string | null;
  max_results_per_leg?: number;
  provider?: string | null;
}

export interface LegResult {
  origin: string;
  destination: string;
  depart_date: string;
  offers: SearchOffer[];
  error: string | null;
}

export interface MultiLegResponse {
  provider: string;
  legs: LegResult[];
  total_min_price: string | null;
  currency: string;
}

export interface SinglePnrLeg {
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
  provider: string;
  provider_offer_id: string;
}

export interface SinglePnrOffer {
  provider: string;
  provider_offer_id: string;
  legs: SinglePnrLeg[];
  total_price: string;
  currency: string;
}

export interface SinglePnrResponse {
  provider: string;
  offers: SinglePnrOffer[];
}

export const searchApi = {
  providers: () => api.get<{ providers: string[] }>('/api/search/providers'),
  flights: (body: SearchInput) => api.post<SearchResponse>('/api/search/flights', body),
  multiLeg: (body: MultiLegInput) => api.post<MultiLegResponse>('/api/search/multi-leg', body),
  multiCitySinglePnr: (body: MultiLegInput) =>
    api.post<SinglePnrResponse>('/api/search/multi-city-single-pnr', body),
  saveOffer: (body: { holiday_id: number; offer: SearchOffer }) =>
    api.post<FlightEntry>('/api/search/save-offer', body),
};
