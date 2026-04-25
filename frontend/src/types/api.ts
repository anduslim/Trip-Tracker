export interface User {
  id: number;
  email: string;
  display_name: string | null;
  created_at: string;
}

export interface Destination {
  city: string;
  iata?: string | null;
  country?: string | null;
}

export interface Holiday {
  id: number;
  user_id: number;
  name: string;
  start_date: string | null;
  end_date: string | null;
  destinations: Destination[];
  notes: string | null;
  currency: string;
  price_change_threshold_pct: string | null;
  price_change_threshold_abs: string | null;
  created_at: string;
  updated_at: string;
}

export interface HolidaySummary extends Holiday {
  flight_entry_count: number;
  lowest_current_price: string | null;
}

export interface HolidayDetail extends Holiday {
  flight_entries: FlightEntry[];
}

export interface FlightEntry {
  id: number;
  holiday_id: number;
  origin_iata: string;
  destination_iata: string;
  depart_date: string;
  return_date: string | null;
  airline_code: string | null;
  airline_name: string | null;
  cabin: string | null;
  passengers: number;
  source_url: string | null;
  source: string;
  initial_price: string;
  latest_price: string;
  currency: string;
  tracking_enabled: boolean;
  last_checked_at: string | null;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface PriceSnapshot {
  id: number;
  flight_entry_id: number;
  price: string;
  currency: string;
  source: string;
  captured_at: string;
}
